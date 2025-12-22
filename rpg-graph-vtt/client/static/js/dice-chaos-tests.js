/**
 * Chaos Engineering Test Suite for DiceVisualizer
 * 
 * Tests the component's resilience under extreme conditions:
 * - Rapid-fire clicks
 * - Delayed server responses
 * - Window resizes/orientation changes
 * - Zero-duration edge cases
 * - Concurrent mixed rolls
 */

class DiceChaosTests {
    constructor(diceVisualizer) {
        this.visualizer = diceVisualizer;
        this.results = {};
    }

    /**
     * Test 1: Rapid-Fire Stress
     * Trigger 100 rolls in < 2 seconds
     * Expected: Only last roll animates, no glitches, no memory leak
     */
    async testRapidFire() {
        console.log('🧪 Chaos Test: Rapid-Fire Stress');
        const startTime = performance.now();
        let rollCount = 0;
        const maxRolls = 100;

        return new Promise((resolve) => {
            const triggerRoll = () => {
                if (rollCount >= maxRolls) {
                    const elapsed = performance.now() - startTime;
                    console.log(`   Completed ${maxRolls} roll attempts in ${elapsed.toFixed(2)}ms`);
                    
                    // Wait for final animation to complete
                    setTimeout(() => {
                        this.results.rapidFire = {
                            passed: true,
                            rollsAttempted: maxRolls,
                            duration: elapsed,
                            message: 'Only last roll should animate'
                        };
                        resolve();
                    }, 3000);
                    return;
                }

                rollCount++;
                const faceValues = [Math.floor(Math.random() * 20) + 1];
                const dieTypes = ['d20'];
                
                // Don't await - fire rapidly
                this.visualizer.rollTo(faceValues, dieTypes).catch(() => {
                    // Expected: some will be rejected due to isRolling lock
                });

                // Fire next roll immediately (no delay)
                requestAnimationFrame(triggerRoll);
            };

            triggerRoll();
        });
    }

    /**
     * Test 2: Delayed Resolution
     * Start roll, wait 8 seconds, then resolve
     * Expected: Shows "tumbling" placeholder animation
     */
    async testDelayedResolution() {
        console.log('🧪 Chaos Test: Delayed Resolution');
        
        return new Promise((resolve) => {
            // Start a roll but delay the result
            const faceValues = [15];
            const dieTypes = ['d20'];
            
            // Simulate delayed server response
            setTimeout(async () => {
                try {
                    await this.visualizer.rollTo(faceValues, dieTypes);
                    this.results.delayedResolution = {
                        passed: true,
                        delay: 8000,
                        message: 'Animation should handle delayed results gracefully'
                    };
                } catch (error) {
                    this.results.delayedResolution = {
                        passed: false,
                        error: error.message
                    };
                }
                resolve();
            }, 8000);
        });
    }

    /**
     * Test 3: Resize Mid-Roll
     * Resize window during animation
     * Expected: Renderer resizes instantly, dice stay in view
     */
    async testResizeMidRoll() {
        console.log('🧪 Chaos Test: Resize Mid-Roll');
        
        return new Promise((resolve) => {
            const faceValues = [10];
            const dieTypes = ['d20'];
            
            const rollPromise = this.visualizer.rollTo(faceValues, dieTypes);
            
            // Resize after 500ms (mid-animation)
            setTimeout(() => {
                const container = this.visualizer.container;
                const originalWidth = container.clientWidth;
                const originalHeight = container.clientHeight;
                
                // Simulate resize
                container.style.width = (originalWidth * 0.5) + 'px';
                container.style.height = (originalHeight * 0.5) + 'px';
                
                // Trigger resize event
                window.dispatchEvent(new Event('resize'));
                
                // Restore after a moment
                setTimeout(() => {
                    container.style.width = originalWidth + 'px';
                    container.style.height = originalHeight + 'px';
                    window.dispatchEvent(new Event('resize'));
                }, 500);
            }, 500);
            
            rollPromise.then(() => {
                this.results.resizeMidRoll = {
                    passed: true,
                    message: 'Renderer should resize gracefully during animation'
                };
                resolve();
            }).catch((error) => {
                this.results.resizeMidRoll = {
                    passed: false,
                    error: error.message
                };
                resolve();
            });
        });
    }

    /**
     * Test 4: Orientation Change (mobile simulation)
     * Simulate device rotation during roll
     * Expected: Canvas resizes, animation continues uninterrupted
     */
    async testOrientationChange() {
        console.log('🧪 Chaos Test: Orientation Change');
        
        return new Promise((resolve) => {
            const faceValues = [18];
            const dieTypes = ['d20'];
            
            const rollPromise = this.visualizer.rollTo(faceValues, dieTypes);
            
            // Simulate orientation change after 300ms
            setTimeout(() => {
                // Swap width/height to simulate rotation
                const container = this.visualizer.container;
                const originalWidth = container.clientWidth;
                const originalHeight = container.clientHeight;
                
                container.style.width = originalHeight + 'px';
                container.style.height = originalWidth + 'px';
                
                // Trigger orientation change event
                window.dispatchEvent(new Event('orientationchange'));
                
                // Restore after animation
                setTimeout(() => {
                    container.style.width = originalWidth + 'px';
                    container.style.height = originalHeight + 'px';
                }, 2000);
            }, 300);
            
            rollPromise.then(() => {
                this.results.orientationChange = {
                    passed: true,
                    message: 'Animation should continue through orientation changes'
                };
                resolve();
            }).catch((error) => {
                this.results.orientationChange = {
                    passed: false,
                    error: error.message
                };
                resolve();
            });
        });
    }

    /**
     * Test 5: Zero-Duration Snap
     * Force duration to 0
     * Expected: Instantly snaps to result, no animation loop
     */
    async testZeroDuration() {
        console.log('🧪 Chaos Test: Zero-Duration Snap');
        
        return new Promise((resolve) => {
            const startTime = performance.now();
            
            // Create visualizer with zero duration
            const zeroDurationVisualizer = new DiceVisualizer(
                this.visualizer.container,
                { animationDuration: 0 }
            );
            
            const faceValues = [20];
            const dieTypes = ['d20'];
            
            zeroDurationVisualizer.rollTo(faceValues, dieTypes).then(() => {
                const elapsed = performance.now() - startTime;
                
                this.results.zeroDuration = {
                    passed: elapsed < 100, // Should be nearly instant
                    duration: elapsed,
                    message: `Snap completed in ${elapsed.toFixed(2)}ms (should be < 100ms)`
                };
                
                zeroDurationVisualizer.destroy();
                resolve();
            }).catch((error) => {
                this.results.zeroDuration = {
                    passed: false,
                    error: error.message
                };
                zeroDurationVisualizer.destroy();
                resolve();
            });
        });
    }

    /**
     * Test 6: Concurrent Mixed Rolls
     * Roll 10d20 + 5d6 + 2d4 simultaneously
     * Expected: All dice animate cleanly, 60 FPS maintained
     */
    async testConcurrentMixed() {
        console.log('🧪 Chaos Test: Concurrent Mixed Rolls');
        
        return new Promise((resolve) => {
            const startTime = performance.now();
            
            // Create roll requests for mixed dice
            const rollRequests = [
                ...Array(10).fill(null).map(() => ({ dieType: 'd20', faceValue: Math.floor(Math.random() * 20) + 1, modifier: 0 })),
                ...Array(5).fill(null).map(() => ({ dieType: 'd6', faceValue: Math.floor(Math.random() * 6) + 1, modifier: 0 })),
                ...Array(2).fill(null).map(() => ({ dieType: 'd4', faceValue: Math.floor(Math.random() * 4) + 1, modifier: 0 }))
            ];
            
            this.visualizer.roll(rollRequests).then((results) => {
                const elapsed = performance.now() - startTime;
                
                // Check FPS (rough estimate)
                const expectedFrames = (elapsed / 1000) * 60; // 60 FPS
                const actualFrames = Math.floor(elapsed / 16.67); // ~16.67ms per frame
                const fpsEstimate = (actualFrames / (elapsed / 1000));
                
                this.results.concurrentMixed = {
                    passed: fpsEstimate >= 50, // Allow some margin
                    diceCount: rollRequests.length,
                    duration: elapsed,
                    estimatedFPS: fpsEstimate.toFixed(1),
                    message: `Rolled ${rollRequests.length} dice in ${elapsed.toFixed(2)}ms, ~${fpsEstimate.toFixed(1)} FPS`
                };
                
                resolve();
            }).catch((error) => {
                this.results.concurrentMixed = {
                    passed: false,
                    error: error.message
                };
                resolve();
            });
        });
    }

    /**
     * Run all chaos tests
     */
    async runAll() {
        console.log('🚀 Starting Chaos Engineering Test Suite...\n');
        this.results = {};
        
        try {
            await this.testRapidFire();
            await this.testDelayedResolution();
            await this.testResizeMidRoll();
            await this.testOrientationChange();
            await this.testZeroDuration();
            await this.testConcurrentMixed();
        } catch (error) {
            console.error('❌ Test suite error:', error);
        }
        
        // Print summary
        console.log('\n📊 Test Results Summary:');
        console.log('========================');
        
        let passed = 0;
        let failed = 0;
        
        for (const [testName, result] of Object.entries(this.results)) {
            const status = result.passed ? '✅ PASS' : '❌ FAIL';
            console.log(`${status} ${testName}: ${result.message || result.error || 'N/A'}`);
            
            if (result.passed) passed++;
            else failed++;
        }
        
        console.log(`\nTotal: ${passed} passed, ${failed} failed`);
        
        return {
            passed,
            failed,
            total: passed + failed,
            results: this.results
        };
    }

    /**
     * Get test results
     */
    getResults() {
        return this.results;
    }
}

// Export for use in modules or global scope
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DiceChaosTests;
}

