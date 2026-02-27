-- Add user moderation/feedback fields to Post nodes
-- Allows marking posts as hidden with reasons and tracking low quality

-- Add hidden flag and moderation reason to Post nodes
MATCH (p:Post)
WHERE p.hidden IS NULL
SET p.hidden = false,
    p.moderation_reason = null,
    p.hidden_flag = null,
    p.user_flags = []
RETURN count(p) as updated_count
