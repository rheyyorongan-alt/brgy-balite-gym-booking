# ⚡ QUICK DEPLOYMENT CHECKLIST

## What We've Done for You ✅
- ✅ Created `vercel.json` - Vercel configuration
- ✅ Updated `settings.py` - Production-ready settings
- ✅ Created `requirements.txt` - All dependencies
- ✅ Created `.env.example` - Environment variables template
- ✅ Created `.gitignore` - Prevents committing sensitive files
- ✅ Added WhiteNoise - Static files handling
- ✅ Added Django-decouple - Environment variable management
- ✅ Added PostgreSQL support - Production database

## Your Deployment Steps (Copy & Paste)

### 1️⃣ Initialize Git and Push to GitHub
```powershell
cd c:\Users\rizza\OneDrive\Desktop\barangay_gym
git init
git add .
git commit -m "Initial commit - ready for Vercel deployment"
git remote add origin https://github.com/YOUR_USERNAME/barangay-gym-booking.git
git branch -M main
git push -u origin main
```

### 2️⃣ Create PostgreSQL Database
Go to https://railway.app or https://vercel.com/storage
- Create PostgreSQL database
- Copy Database URL
- Save it (you'll need it soon)

### 3️⃣ Generate Secret Key
```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
Save the output.

### 4️⃣ Go to Vercel and Deploy
1. Go to https://vercel.com/dashboard
2. Click "Add New Project"
3. Import your GitHub repository
4. Add environment variables:
   - `SECRET_KEY` = (from step 3)
   - `DEBUG` = `False`
   - `ALLOWED_HOSTS` = `your-domain.vercel.app`
   - `DATABASE_URL` = (from step 2)
   - `CSRF_TRUSTED_ORIGINS` = `https://your-domain.vercel.app`
5. Click "Deploy"

### 5️⃣ Run Migrations (After Deployment)
```powershell
npm install -g vercel
vercel login
cd c:\Users\rizza\OneDrive\Desktop\barangay_gym
vercel env pull
python manage.py migrate --no-input
```

### 6️⃣ Create Admin User
```powershell
python manage.py createsuperuser
# OR
python manage.py shell
# from django.contrib.auth.models import User
# User.objects.create_superuser('admin', 'admin@gym.com', 'YourPassword123')
```

### 7️⃣ Test Your Live Site
- Open: https://your-domain.vercel.app
- Login with admin credentials
- Visit admin panel: https://your-domain.vercel.app/admin

## Important Naming Convention

When asked "what to name this on Vercel", use:
- **Project Name**: `barangay-gym-booking` (or `barangay-gym` for shorter name)
- **Domain**: `barangay-gym-booking.vercel.app` (automatic)
- **Database**: `barangay-gym-db`
- **GitHub Repo**: `barangay-gym-booking`

## File What We Created/Updated

| File | Purpose |
|------|---------|
| `vercel.json` | Tells Vercel how to deploy Django |
| `requirements.txt` | Lists all Python dependencies |
| `.env.example` | Template for environment variables |
| `gym_booking/settings.py` | Production-ready Django settings |
| `.gitignore` | Prevents sensitive files from being pushed |
| `VERCEL_DEPLOYMENT_GUIDE.md` | Detailed step-by-step guide |

## Need Help?

❌ **502 Bad Gateway?** → Check Vercel deployment logs
❌ **Can't upload files?** → Run `python manage.py collectstatic --noinput`
❌ **Login doesn't work?** → Verify superuser was created
❌ **Database errors?** → Check DATABASE_URL in Vercel env variables

Read the full `VERCEL_DEPLOYMENT_GUIDE.md` for detailed troubleshooting!
