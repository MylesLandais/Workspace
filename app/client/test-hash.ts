export {};

const start = Date.now();
const password = "password123";
const salt = crypto.getRandomValues(new Uint8Array(16));
console.log("Starting hash...");
// Simulate what better-auth might be doing
const hash = await Bun.password.hash(password);
console.log(`Hash completed in ${Date.now() - start}ms`);
const match = await Bun.password.verify(password, hash);
console.log(`Verify completed in ${Date.now() - start}ms (match: ${match})`);
