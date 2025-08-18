# Railway Template Contribution Strategy

## Overview

This document outlines our hybrid contribution strategy for maintaining Railway deployment templates while contributing valuable improvements back to the Trigger.dev upstream project.

## Current Strategy: Hybrid Contribution Model

We're using a **hybrid contribution strategy** that allows us to:
1. **Ship Railway templates immediately** with all improvements
2. **Plan upstream contributions** for universally valuable fixes
3. **Maintain version-specific Railway templates** for different Trigger.dev releases

## Branch Structure

```
nick0lay/trigger.dev (our fork)
├── main                                    # Our main branch
├── feature/DEV-*                          # Development branches
├── railway-template-v4.0.0                # v4.0.0 with Railway + all improvements
├── railway-template-v4.0.1                # Future v4.0.1 release
└── railway-template-v5.0.0                # Future v5.0.0 release
```

**Important**: Branch names use hyphens (`-`) not slashes (`/`) to ensure Railway's URL parser correctly identifies the full branch name.

## Types of Changes

### 1. Core Improvements (Upstream Candidates)
These are universally valuable fixes that benefit all Trigger.dev deployments:

- **IPv6 Redis DNS fixes** (`family: 0` in Redis configuration)
  - Files: `internal-packages/redis/src/index.ts`, various `redis.server.ts` files
  - Benefit: Fixes Redis connectivity in IPv6-only environments (Railway, Render, modern Docker)
  
- **Migration optimization** (baseline SQL approach)
  - Files: `.railway/migrate.sh`, `.railway/baseline.sql`
  - Benefit: Reduces migration time from 20+ minutes to ~1 minute

### 2. Railway-Specific Files
These are deployment-specific configurations for Railway platform:

- `railway.json` - Railway deployment configuration
- `.railway/` directory - Railway-specific scripts and documentation
- `RAILWAY.md` - Railway deployment guide
- `nixpacks.toml` - Build configuration for Railway

## Workflow for New Versions

### When upstream releases a new version (e.g., v4.0.1):

1. **Fetch upstream tags**
   ```bash
   git fetch upstream --tags
   ```

2. **Create new template branch from upstream tag**
   ```bash
   git checkout -b railway-template-v4.0.1 trigger.dev@4.0.1
   ```

3. **Merge our improvements**
   ```bash
   git merge railway-template-v4.0.0
   # Resolve conflicts if any (keep upstream core, our Railway files)
   ```

4. **Test and push**
   ```bash
   git push origin railway-template-v4.0.1
   ```

5. **Update Railway template** to point to new branch

## Conflict Resolution Strategy

When merging upstream changes:

| File Type | Resolution Strategy |
|-----------|-------------------|
| **Core application code** | Accept upstream changes |
| **Railway-specific files** | Keep our version |
| **Shared files** (package.json, etc.) | Manual review |

### Priority Order:
1. ✅ **Keep upstream**: Core code, features, dependencies
2. ✅ **Keep ours**: Railway files, deployment configs
3. ⚡ **Manual review**: Files affecting both

## Future Upstream Contribution Plan

### Phase 1: Immediate (Completed)
- ✅ Created `railway-template-v4.0.0` with all improvements
- ✅ Railway template deployed and working
- ✅ Users get immediate value

### Phase 2: Short-term (Planned)
- [ ] Extract core improvements into separate branch
- [ ] Create clean PR for IPv6 Redis fixes
- [ ] Create separate PR for migration optimization
- [ ] Engage with upstream maintainers

### Phase 3: Long-term
- [ ] Once upstream adopts core fixes, simplify Railway templates
- [ ] Railway templates become pure overlay (just deployment configs)
- [ ] Reduced maintenance burden

## Upstream Contribution Preparation

### For IPv6 Redis Fixes:
```bash
# Create clean branch for upstream
git checkout -b upstream/redis-ipv6-fixes main
git cherry-pick <specific-redis-fix-commits>

# Files to include:
# - internal-packages/redis/src/index.ts (family: 0 addition)
# - Various redis.server.ts files with family: 0
```

### PR Description Template:
```markdown
## Fix Redis connectivity in IPv6-only environments

### Problem
Redis connections fail in IPv6-only environments (Railway, Render, modern Docker) because ioredis defaults to IPv4-only DNS lookups.

### Solution
Add `family: 0` to Redis options, enabling dual-stack IPv4/IPv6 DNS resolution.

### Testing
- Tested on Railway platform (IPv6-only internal networking)
- Backwards compatible with IPv4-only environments
- No breaking changes

### Files Changed
- `internal-packages/redis/src/index.ts` - Default options for all Redis clients
- Various `redis.server.ts` files - Specific Redis client instances
```

## Benefits of This Strategy

### Immediate Benefits
- ✅ Railway templates ship today with full features
- ✅ Users get working deployment immediately
- ✅ No waiting for upstream review cycles

### Long-term Benefits
- 🌍 Core improvements benefit entire community
- 🔄 Reduced maintenance burden once upstream adopts
- 🤝 Good open source citizenship
- 📈 Potential for becoming official Railway deployment method

## Maintenance Guidelines

1. **Always test** Railway deployment after creating new version branches
2. **Document changes** in commit messages and PR descriptions
3. **Keep Railway-specific files minimal** to reduce merge conflicts
4. **Engage with upstream** maintainers for core improvements
5. **Monitor upstream releases** for new versions

## Automation Opportunities

Consider creating scripts for:
- Automated version branch creation
- Conflict resolution helpers
- Template testing automation
- Upstream PR preparation

## Contact

For questions about this strategy or Railway templates:
- GitHub: @nick0lay
- Railway Templates: https://github.com/nick0lay/trigger.dev/tree/railway-template-v4.0.0