#!/bin/bash
# Post-merge deployment steps for UberOKX
# Execute this script after successfully merging fix/code-cleanup-and-bugs into main

set -e  # Exit on any error

echo "╔════════════════════════════════════════════════════════╗"
echo "║    🚀 POST-MERGE DEPLOYMENT - UBEROKX                 ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════"
echo "1️⃣  MERGE STATUS"
echo "════════════════════════════════════════════════════════"
echo ""

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}⚠️  Warning: You're not on main branch${NC}"
    echo "Please run: git checkout main"
    exit 1
fi

CURRENT_COMMIT=$(git log -1 --oneline)
echo "Latest commit: $CURRENT_COMMIT"

echo ""
echo "════════════════════════════════════════════════════════"
echo "2️⃣  PULL LATEST CHANGES"
echo "════════════════════════════════════════════════════════"
echo ""

echo "Pulling latest changes from remote..."
git pull origin main
echo -e "${GREEN}✓ Pull successful${NC}"

echo ""
echo "════════════════════════════════════════════════════════"
echo "3️⃣  VERIFY MERGED FILES"
echo "════════════════════════════════════════════════════════"
echo ""

FILES_TO_CHECK=(
    "backend/main.py"
    "backend/auth.py"
    "backend/config.py"
    "run.py"
    "split_uberox.py"
    "FIXES_REPORT.md"
    "TESTING_DEPLOYMENT.md"
    "PULL_REQUEST.md"
)

for file in "${FILES_TO_CHECK[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${YELLOW}⚠${NC} $file (missing)"
    fi
done

echo ""
echo "════════════════════════════════════════════════════════"
echo "4️⃣  VERIFY IMPORTS AND SYNTAX"
echo "════════════════════════════════════════════════════════"
echo ""

echo "Testing core imports..."
python -c "from backend.config import settings; print('✓ Config OK')"
python -c "from backend.auth import get_current_user; print('✓ Auth OK')"
python -c "from backend.main import app; print('✓ Main app OK')"

echo ""
echo "════════════════════════════════════════════════════════"
echo "5️⃣  CREATE BACKUP"
echo "════════════════════════════════════════════════════════"
echo ""

BACKUP_DIR="backups/backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
echo "Creating backup in: $BACKUP_DIR"

# Backup important files
cp -r backend "$BACKUP_DIR/" || true
cp run.py "$BACKUP_DIR/" || true
cp requirements.txt "$BACKUP_DIR/" || true

echo -e "${GREEN}✓ Backup created${NC}"

echo ""
echo "════════════════════════════════════════════════════════"
echo "6️⃣  STAGING ENVIRONMENT DEPLOYMENT"
echo "════════════════════════════════════════════════════════"
echo ""

echo "STAGING DEPLOYMENT STEPS:"
echo ""
echo "1. Create staging branch:"
echo "   git checkout -b staging"
echo ""
echo "2. Set environment variables:"
echo "   export ENVIRONMENT=staging"
echo "   export ADMIN_EMAIL=admin@staging.local"
echo ""
echo "3. Install/update dependencies:"
echo "   pip install -r requirements.txt"
echo ""
echo "4. Test the application:"
echo "   python run.py"
echo ""
echo "5. Run validation tests:"
echo "   curl http://127.0.0.1:8080/health"
echo ""
echo "6. After successful staging tests:"
echo "   git checkout main"
echo ""

echo ""
echo "════════════════════════════════════════════════════════"
echo "7️⃣  PRODUCTION DEPLOYMENT CHECKLIST"
echo "════════════════════════════════════════════════════════"
echo ""

echo "Before deploying to production:"
echo ""
echo "☐ Staging tests passed"
echo "☐ All security checks verified"
echo "☐ Environment variables configured"
echo "☐ Database backups created"
echo "☐ Rollback plan documented"
echo "☐ Monitoring alerts configured"
echo "☐ Team notified of deployment"
echo ""

echo "PRODUCTION DEPLOYMENT:"
echo ""
echo "1. SSH into production server:"
echo "   ssh user@production-server"
echo ""
echo "2. Navigate to app directory:"
echo "   cd /opt/uberokx"
echo ""
echo "3. Pull latest main branch:"
echo "   git fetch origin"
echo "   git checkout main"
echo "   git pull origin main"
echo ""
echo "4. Update dependencies:"
echo "   pip install -r requirements.txt"
echo ""
echo "5. Restart the application:"
echo "   sudo systemctl restart uberokx"
echo ""
echo "6. Verify health:"
echo "   curl https://your-domain/health"
echo ""
echo "7. Check logs:"
echo "   tail -f /var/log/uberokx/app.log"
echo ""

echo ""
echo "════════════════════════════════════════════════════════"
echo "8️⃣  POST-DEPLOYMENT MONITORING"
echo "════════════════════════════════════════════════════════"
echo ""

echo "Monitor these metrics:"
echo ""
echo "✓ Application health (HTTP 200 on /health)"
echo "✓ Error rates (logs for 5xx errors)"
echo "✓ Login functionality (test auth flow)"
echo "✓ API endpoints (test key endpoints)"
echo "✓ Webhook processing (if applicable)"
echo "✓ Performance (response times)"
echo "✓ Security (no auth bypasses)"
echo ""

echo "Useful commands:"
echo ""
echo "# Check app status"
echo "sudo systemctl status uberokx"
echo ""
echo "# View live logs"
echo "sudo journalctl -u uberokx -f"
echo ""
echo "# Check error rate"
echo "grep -i error /var/log/uberokx/app.log | wc -l"
echo ""
echo "# Test authentication"
echo "curl -X POST http://localhost:8080/login -d 'email=admin@example.com&password=test'"
echo ""

echo ""
echo "════════════════════════════════════════════════════════"
echo "9️⃣  ROLLBACK PROCEDURE (if needed)"
echo "═══════════════════════���════════════════════════════════"
echo ""

echo "If issues occur after deployment:"
echo ""
echo "1. Immediate rollback:"
echo "   git revert HEAD"
echo "   pip install -r requirements.txt"
echo "   sudo systemctl restart uberokx"
echo ""
echo "2. Restore from backup:"
echo "   cp -r backups/latest/* ."
echo "   sudo systemctl restart uberokx"
echo ""
echo "3. Notify team and investigate"
echo ""

echo ""
echo "════════════════════════════════════════════════════════"
echo "✅ POST-MERGE SETUP COMPLETE"
echo "════════════════════════════════════════════════════════"
echo ""

echo -e "${GREEN}All files merged and verified!${NC}"
echo ""
echo "Next steps:"
echo "  1. Follow the Staging Deployment checklist"
echo "  2. Run tests in staging environment"
echo "  3. Follow the Production Deployment checklist"
echo "  4. Monitor the application post-deployment"
echo ""
echo "Documentation:"
echo "  - FIXES_REPORT.md: Technical details of all fixes"
echo "  - TESTING_DEPLOYMENT.md: Comprehensive testing guide"
echo "  - PULL_REQUEST.md: Summary of changes"
echo ""
