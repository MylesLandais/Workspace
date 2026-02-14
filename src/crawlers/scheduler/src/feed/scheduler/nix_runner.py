"""Nix-shell execution wrapper with hash-based environment caching.

Provides fast, reproducible Python script execution by pre-building and caching
nix-shell environments based on package specification hashes.
"""

import subprocess
import json
import hashlib
import os
import tempfile
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timezone as tz
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class NixRunner:
    """Execute Python scripts in cached nix-shell environments."""

    def __init__(self, postgres_connection=None, nix_store_path: str = "/nix/store"):
        """Initialize NixRunner with optional PostgreSQL connection for caching.

        Args:
            postgres_connection: PostgresConnection instance for environment caching
            nix_store_path: Path to nix store (usually /nix/store)
        """
        self.pg = postgres_connection
        self.nix_store_path = nix_store_path

    @staticmethod
    def hash_package_spec(packages: List[str]) -> str:
        """Generate SHA256 hash from sorted package specification.

        Args:
            packages: List of nix package identifiers (e.g., ["python3", "python3Packages.praw"])

        Returns:
            Hex SHA256 hash of sorted, JSON-serialized package list
        """
        sorted_packages = sorted(packages)
        spec_json = json.dumps(sorted_packages, separators=(",", ":"))
        return hashlib.sha256(spec_json.encode()).hexdigest()

    def _generate_shell_nix(self, packages: List[str]) -> str:
        """Generate shell.nix content for package specification.

        Args:
            packages: List of nix packages

        Returns:
            String content of shell.nix
        """
        packages_str = ", ".join(f'"{pkg}"' for pkg in packages)

        template = f"""{{ pkgs ? import <nixpkgs> {{}} }}:
pkgs.mkShell {{
  buildInputs = with pkgs; [
    {packages_str}
  ];
}}
"""
        return template

    def _get_shell_nix_path(self, hash_val: str) -> Path:
        """Get temporary path for shell.nix based on hash."""
        tmpdir = Path(tempfile.gettempdir()) / "jupyter-nix-shells"
        tmpdir.mkdir(parents=True, exist_ok=True)
        return tmpdir / f"shell-{hash_val}.nix"

    def get_or_build_shell(self, packages: List[str]) -> Tuple[str, bool]:
        """Get or build nix-shell environment, returning derivation path.

        Implements cache lookup in PostgreSQL nix_environments table:
        1. Hash the package spec
        2. Query database for cached environment
        3. On cache hit: update use_count and return .drv path
        4. On cache miss: generate shell.nix, instantiate, realize, store in DB

        Args:
            packages: List of nix packages to include

        Returns:
            Tuple of (drv_path: str, was_cached: bool)

        Raises:
            RuntimeError: If nix-instantiate or nix-store fails
        """
        hash_val = self.hash_package_spec(packages)

        # Try cache lookup if PostgreSQL available
        if self.pg:
            try:
                result = self.pg.execute_read(
                    "SELECT drv_path, use_count FROM nix_environments WHERE hash = %s",
                    (hash_val,)
                )
                if result:
                    drv_path, use_count = result[0]
                    # Update use count and last_used_at
                    self.pg.execute_write(
                        """
                        UPDATE nix_environments
                        SET use_count = use_count + 1, last_used_at = %s
                        WHERE hash = %s
                        """,
                        (datetime.now(tz.utc), hash_val)
                    )
                    logger.info(
                        f"Cache hit for nix environment {hash_val[:8]} "
                        f"(use_count: {use_count + 1})"
                    )
                    return drv_path, True
            except Exception as e:
                logger.warning(f"Database cache lookup failed: {e}")

        # Cache miss - build new environment
        logger.info(f"Building new nix environment for {len(packages)} packages (hash: {hash_val[:8]})")
        shell_nix_path = self._get_shell_nix_path(hash_val)

        # Generate shell.nix
        shell_nix_content = self._generate_shell_nix(packages)
        shell_nix_path.write_text(shell_nix_content)
        logger.debug(f"Generated shell.nix at {shell_nix_path}")

        # Instantiate to get .drv file
        try:
            result = subprocess.run(
                ["nix-instantiate", str(shell_nix_path)],
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=True,
            )
            drv_path = result.stdout.strip()
            logger.info(f"Instantiated nix environment: {drv_path}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"nix-instantiate failed: {e.stderr}"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(
                f"nix-instantiate timed out after 300s"
            ) from e

        # Realize (build) the environment
        try:
            result = subprocess.run(
                ["nix-store", "--realize", drv_path],
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
                check=True,
            )
            store_path = result.stdout.strip()
            logger.info(f"Built nix environment at {store_path}")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"nix-store --realize failed: {e.stderr}"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(
                f"nix-store --realize timed out after 600s"
            ) from e

        # Store in database for future cache hits
        if self.pg:
            try:
                self.pg.execute_write(
                    """
                    INSERT INTO nix_environments (hash, packages, drv_path, store_path, use_count)
                    VALUES (%s, %s, %s, %s, 1)
                    ON CONFLICT (hash) DO UPDATE
                    SET use_count = nix_environments.use_count + 1, last_used_at = %s
                    """,
                    (
                        hash_val,
                        json.dumps(packages),
                        drv_path,
                        store_path,
                        datetime.now(tz.utc),
                    )
                )
                logger.debug(f"Stored nix environment {hash_val[:8]} in database")
            except Exception as e:
                logger.warning(f"Failed to store nix environment in database: {e}")

        return drv_path, False

    def run_script(
        self,
        script_path: str,
        packages: List[str],
        args: Optional[List[str]] = None,
        working_dir: Optional[str] = None,
        env_vars: Optional[Dict[str, str]] = None,
    ) -> Dict:
        """Execute Python script in nix-shell environment.

        Builds environment if needed, then executes:
        nix-shell <drv> --pure --run "python script.py --args"

        Args:
            script_path: Path to Python script to execute
            packages: List of nix packages needed (e.g., ["python3", "python3Packages.praw"])
            args: Optional list of command-line arguments for the script
            working_dir: Optional working directory for script execution
            env_vars: Optional environment variables to set

        Returns:
            Dict with execution results:
            {
                "success": bool,
                "stdout": str,
                "stderr": str,
                "exit_code": int,
                "duration_ms": int,
                "environment_hash": str,
                "was_cached": bool,
                "drv_path": str,
            }

        Raises:
            FileNotFoundError: If script_path doesn't exist
        """
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")

        # Get or build environment
        start_time = datetime.now(tz.utc)
        drv_path, was_cached = self.get_or_build_shell(packages)
        build_time = (datetime.now(tz.utc) - start_time).total_seconds() * 1000

        # Build command
        script_args = " ".join(args) if args else ""
        command = f"python {script_path}"
        if script_args:
            command += f" {script_args}"

        # Prepare environment
        exec_env = os.environ.copy()
        if env_vars:
            exec_env.update(env_vars)

        # Execute in nix-shell
        nix_cmd = [
            "nix-shell",
            drv_path,
            "--pure",
            "--run",
            command,
        ]

        try:
            exec_start = datetime.now(tz.utc)
            result = subprocess.run(
                nix_cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                cwd=working_dir or os.getcwd(),
                env=exec_env,
            )
            exec_time = (datetime.now(tz.utc) - exec_start).total_seconds() * 1000

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode,
                "duration_ms": int(exec_time),
                "build_time_ms": int(build_time),
                "environment_hash": self.hash_package_spec(packages),
                "was_cached": was_cached,
                "drv_path": drv_path,
            }
        except subprocess.TimeoutExpired as e:
            logger.error(f"Script execution timed out after 3600s: {script_path}")
            return {
                "success": False,
                "stdout": e.stdout or "",
                "stderr": "Script execution timed out after 3600 seconds",
                "exit_code": 124,  # Standard timeout exit code
                "duration_ms": 3600000,
                "build_time_ms": int(build_time),
                "environment_hash": self.hash_package_spec(packages),
                "was_cached": was_cached,
                "drv_path": drv_path,
            }
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "exit_code": 127,  # Command not found exit code
                "duration_ms": 0,
                "build_time_ms": int(build_time),
                "environment_hash": self.hash_package_spec(packages),
                "was_cached": was_cached,
                "drv_path": drv_path,
            }

    def cleanup_stale_environments(self, days: int = 30) -> int:
        """Delete nix environments unused for N days from database.

        Note: This only removes database entries. Actual nix store entries
        are managed by nix garbage collection.

        Args:
            days: Number of days of inactivity before deletion

        Returns:
            Number of environments deleted
        """
        if not self.pg:
            logger.warning("PostgreSQL connection not available for cleanup")
            return 0

        try:
            result = self.pg.execute_write(
                """
                DELETE FROM nix_environments
                WHERE last_used_at < NOW() - INTERVAL '%s days'
                """,
                (days,)
            )
            deleted_count = result if isinstance(result, int) else 0
            logger.info(f"Cleaned up {deleted_count} stale nix environments (older than {days} days)")
            return deleted_count
        except Exception as e:
            logger.error(f"Error during environment cleanup: {e}")
            return 0
