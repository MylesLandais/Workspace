export function getBucketKey(phash: bigint, bits: number = 16): string {
  const mask = (1n << BigInt(bits)) - 1n;
  const highBits = (phash >> BigInt(64 - bits)) & mask;
  return `phash:bucket:${highBits.toString(16).padStart(4, '0')}`;
}

export function getBucketKeys(phash: bigint, bits: number = 16): string[] {
  const baseKey = getBucketKey(phash, bits);
  const keys = [baseKey];
  
  const highBits = (phash >> BigInt(64 - bits)) & ((1n << BigInt(bits)) - 1n);
  
  for (let i = 0; i < bits; i++) {
    const bitMask = 1n << BigInt(bits - 1 - i);
    const flipped = highBits ^ bitMask;
    const key = `phash:bucket:${flipped.toString(16).padStart(4, '0')}`;
    if (key !== baseKey) {
      keys.push(key);
    }
  }
  
  return keys;
}

export function hammingDistance(hash1: bigint, hash2: bigint): number {
  const xor = hash1 ^ hash2;
  let distance = 0;
  let value = xor;
  
  while (value > 0n) {
    distance += Number(value & 1n);
    value >>= 1n;
  }
  
  return distance;
}

