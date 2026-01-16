"""Puppeteer E2E test setup and utilities."""

import os
import asyncio
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from pyppeteer import launch, Browser, Page
    PUPPETEER_AVAILABLE = True
except ImportError:
    PUPPETEER_AVAILABLE = False
    print("Warning: pyppeteer not installed. Install with: pip install pyppeteer")


class PuppeteerTestBase:
    """Base class for Puppeteer E2E tests."""
    
    def __init__(self, headless: bool = True, slow_mo: int = 0):
        """
        Initialize Puppeteer test base.
        
        Args:
            headless: Run browser in headless mode
            slow_mo: Slow down operations by N ms (for debugging)
        """
        self.headless = headless
        self.slow_mo = slow_mo
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    async def setup(self):
        """Set up browser and page."""
        if not PUPPETEER_AVAILABLE:
            raise ImportError("pyppeteer not installed")
        
        self.browser = await launch(
            headless=self.headless,
            slowMo=self.slow_mo,
            args=['--no-sandbox', '--disable-setuid-sandbox'],
        )
        self.page = await self.browser.newPage()
        
        # Set viewport
        await self.page.setViewport({'width': 1920, 'height': 1080})
    
    async def teardown(self):
        """Clean up browser."""
        if self.browser:
            await self.browser.close()
    
    async def navigate(self, url: str):
        """Navigate to URL."""
        if not self.page:
            raise RuntimeError("Page not initialized. Call setup() first.")
        await self.page.goto(url, waitUntil='networkidle2')
    
    async def screenshot(self, filename: str):
        """Take screenshot."""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        await self.page.screenshot({'path': filename})
    
    async def wait_for_selector(self, selector: str, timeout: int = 30000):
        """Wait for selector to appear."""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        await self.page.waitForSelector(selector, timeout=timeout)
    
    async def click(self, selector: str):
        """Click element."""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        await self.page.click(selector)
    
    async def type_text(self, selector: str, text: str):
        """Type text into input."""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        await self.page.type(selector, text)
    
    async def get_text(self, selector: str) -> str:
        """Get text content of element."""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        element = await self.page.querySelector(selector)
        if element:
            return await self.page.evaluate('(element) => element.textContent', element)
        return ""
    
    async def evaluate(self, script: str) -> Any:
        """Evaluate JavaScript in page context."""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        return await self.page.evaluate(script)
    
    async def wait_for_navigation(self, timeout: int = 30000):
        """Wait for navigation."""
        if not self.page:
            raise RuntimeError("Page not initialized.")
        await self.page.waitForNavigation(timeout=timeout, waitUntil='networkidle2')


class GraphQLTestClient:
    """Client for testing GraphQL API."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        """
        Initialize GraphQL test client.
        
        Args:
            base_url: Base URL of GraphQL server
        """
        self.base_url = base_url
        self.graphql_url = f"{base_url}/graphql"
    
    async def query(self, query: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute GraphQL query.
        
        Args:
            query: GraphQL query string
            variables: Optional variables dict
        
        Returns:
            Response dict with 'data' and/or 'errors'
        """
        import aiohttp
        
        payload = {
            "query": query,
        }
        if variables:
            payload["variables"] = variables
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.graphql_url,
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:
                return await response.json()
    
    async def mutation(self, mutation: str, variables: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute GraphQL mutation (same as query)."""
        return await self.query(mutation, variables)




