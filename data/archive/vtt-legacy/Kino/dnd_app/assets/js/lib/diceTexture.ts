// Premium dice skin presets
export type DiceSkin = 'premium-gold' | 'classic-red' | 'obsidian' | 'emerald' | 'sapphire' | 'custom';

export interface DiceSkinConfig {
    textColor: string;
    backgroundColor: string;
    borderColor: string;
    shadowIntensity: number;
    texturePattern?: string; // URL to texture image
}

export const DICE_SKINS: Record<DiceSkin, DiceSkinConfig> = {
    'premium-gold': {
        textColor: '#FFD700',
        backgroundColor: 'rgba(0,0,0,0)',
        borderColor: 'rgba(255,215,0,0.3)',
        shadowIntensity: 0.6,
    },
    'classic-red': {
        textColor: '#FFFFFF',
        backgroundColor: '#E00000',
        borderColor: 'rgba(0,0,0,0.2)',
        shadowIntensity: 0.5,
    },
    'obsidian': {
        textColor: '#FFFFFF',
        backgroundColor: '#1C1C1C',
        borderColor: 'rgba(255,255,255,0.1)',
        shadowIntensity: 0.8,
    },
    'emerald': {
        textColor: '#50C878',
        backgroundColor: 'rgba(0,0,0,0)',
        borderColor: 'rgba(80,200,120,0.3)',
        shadowIntensity: 0.6,
    },
    'sapphire': {
        textColor: '#4169E1',
        backgroundColor: 'rgba(0,0,0,0)',
        borderColor: 'rgba(65,105,225,0.3)',
        shadowIntensity: 0.6,
    },
    'custom': {
        textColor: 'white',
        backgroundColor: '#E00000',
        borderColor: 'rgba(0,0,0,0.2)',
        shadowIntensity: 0.5,
    },
};

export function createDiceTexture(
    number: number | string,
    skin: DiceSkin = 'premium-gold',
    customConfig?: Partial<DiceSkinConfig>
): string | null {
    const config = { ...DICE_SKINS[skin], ...customConfig };
    
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128; // Power of 2
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    // Apply texture pattern if provided
    if (config.texturePattern) {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        // Note: In production, load texture asynchronously or preload
    }

    // Background with gradient for premium look
    if (config.backgroundColor !== 'rgba(0,0,0,0)') {
        ctx.fillStyle = config.backgroundColor;
        ctx.fillRect(0, 0, 128, 128);
        
        // Add subtle gradient for depth
        const gradient = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
        gradient.addColorStop(0, 'rgba(255,255,255,0.1)');
        gradient.addColorStop(1, 'rgba(0,0,0,0.2)');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 128, 128);
    }

    // Premium border with glow effect
    ctx.strokeStyle = config.borderColor;
    ctx.lineWidth = 8;
    ctx.shadowColor = config.textColor;
    ctx.shadowBlur = 4;
    ctx.strokeRect(4, 4, 120, 120);

    // Text with premium styling
    ctx.fillStyle = config.textColor;
    ctx.font = 'bold 90px "Outfit", "Inter", "Arial", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Enhanced shadow for depth
    ctx.shadowColor = 'rgba(0, 0, 0, 0.8)';
    ctx.shadowBlur = 6 * config.shadowIntensity;
    ctx.shadowOffsetX = 2;
    ctx.shadowOffsetY = 2;

    ctx.translate(64, 64);
    
    // Add text glow effect for premium skins
    if (skin === 'premium-gold' || skin === 'emerald' || skin === 'sapphire') {
        ctx.shadowColor = config.textColor;
        ctx.shadowBlur = 8;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
    }
    
    ctx.fillText(String(number), 0, 0);

    return canvas.toDataURL();
}

// Legacy function for backward compatibility
export function createDiceTextureLegacy(number: number | string, color: string = 'white', bgColor: string = '#E00000') {
    return createDiceTexture(number, 'custom', { textColor: color, backgroundColor: bgColor });
}

