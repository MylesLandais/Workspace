export function getBucketKey(phash: bigint, bits: number = 16): string {
  if (typeof phash !== 'bigint') {
    throw new Error(`phash must be bigint, got ${typeof phash}: ${phash}`);
  }
  const bitsBigInt = BigInt(bits);
  const mask = (1n << bitsBigInt) - 1n;
  const shift = 64n - bitsBigInt;
  const shifted = phash >> shift;
  const highBits = shifted & mask;
  const hexString = highBits.toString(16);
  const paddedHex = hexString.padStart(4, '0');
  return `phash:bucket:${paddedHex}`;
}

export function getBucketKeys(phash: bigint, bits: number = 16): string[] {
  const baseKey = getBucketKey(phash, bits);
  const keys = [baseKey];

  const bitsBigInt = BigInt(bits);
  const highBits = (phash >> (64n - bitsBigInt)) & ((1n << bitsBigInt) - 1n);

  for (let i = 0; i < bits; i++) {
    const bitMask = 1n << (bitsBigInt - 1n - BigInt(i));
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

