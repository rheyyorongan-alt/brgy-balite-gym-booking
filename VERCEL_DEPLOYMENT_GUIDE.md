# 🚀 VERCEL DEPLOYMENT GUIDE - BARANGAY GYM BOOKING SYSTEM

## 📋 PREREQUISITES

Before starting, you need:
- ✅ Git installed on your computer
- ✅ GitHub, GitLab, or Bitbucket account (for version control)
- ✅ Vercel account (https://vercel.com - FREE)
- ✅ Railway.app or Vercel Postgres account (for PostgreSQL database)

---

## 📝 STEP-BY-STEP DEPLOYMENT

### **STEP 1: Initialize Git Repository**

If you haven't already, initialize Git in your project:

```bash
cd c:\Users\rizza\OneDrive\Desktop\barangay_gym
git init
git add .
git commit -m "Initial commit - ready for Vercel deployment"
```

### **STEP 2: Push to GitHub**

1. Create a **NEW repository** on GitHub (https://github.com/new)
   - Name it: `barangay-gym-booking` (or your preferred name)
   - Description: "Barangay Gym Booking Management System"
   - Make it **PUBLIC** (Vercel free tier works better with public repos)
   - DO NOT initialize with README, .gitignore, or license

2. In your terminal, add GitHub as remote and push:

```bash
git remote add origin https://github.com/YOUR_USERNAME/barangay-gym-booking.git
git branch -M main
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

---

### **STEP 3: Set Up PostgreSQL Database**

**Option A: Using Railway.app (RECOMMENDED - Easiest)**

1. Go to https://railway.app
2. Sign up with GitHub
3. Click **"Start a New Project"**
4. Select **"Provision PostgreSQL"**
5. Click on the PostgreSQL database
6. Go to **"Connect"** tab
7. Copy the **Database URL** (looks like: `postgresql://...`)
8. **Save this URL** - you'll need it in Step 5

**Option B: Using Vercel Postgres**

1. Go to https://vercel.com/dashboard
2. Click **"Storage"** tab
3. Click **"Create"** → **"Postgres"**
4. Name it: `barangay-gym-db`
5. Copy the **Database URL**
6. **Save this URL** - you'll need it in Step 5

---

### **STEP 4: Generate Secret Key**

Run this Python command to generate a secure SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Save the output** - you'll need it in Step 5.

---

### **STEP 5: Set Up Vercel Project**

1. Go to https://vercel.com/dashboard
2. Click **"Add New Project"**
3. Click **"Import Git Repository"**
4. Find and select `barangay-gym-booking` from GitHub
5. Click **"Import"**
6. **PROJECT NAME**: Type `barangay-gym-booking` (or your preferred name)
7. Click **"Continue"**

---

### **STEP 6: Configure Environment Variables**

In the Vercel deployment settings, add these environment variables:

| Variable | Value | Example |
|----------|-------|---------|
| `SECRET_KEY` | Paste the key from Step 4 | `django-insecure-abc123...` |
| `DEBUG` | `False` | `False` |
| `ALLOWED_HOSTS` | Your Vercel domain(s) | `yourdomain.vercel.app,www.yourdomain.com` |
| `DATABASE_URL` | Paste from Step 3 | `postgresql://user:pass@...` |
| `CSRF_TRUSTED_ORIGINS` | Same as ALLOWED_HOSTS | `https://yourdomain.vercel.app,https://www.yourdomain.com` |

**Steps to add:**
1. In Vercel dashboard → Project → **Settings** → **Environment Variables**
2. Click **"Add New"**
3. Fill in Name and Value
4. Click **"Save**
5. Repeat for each variable above

---

### **STEP 7: Deploy to Vercel**

1. Go back to the Vercel dashboard
2. Click the project: `barangay-gym-booking`
3. Click **"Deploy"** button
4. **Wait for deployment** (takes 2-5 minutes)
5. When done, you'll see: ✅ **"Domains"** with your live URL

---

### **STEP 8: Run Database Migrations**

After deployment, you need to migrate the database.

**Option 1: Using Vercel CLI (Recommended)**

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Navigate to project
cd c:\Users\rizza\OneDrive\Desktop\barangay_gym

# Run migrations
vercel env pull
python manage.py migrate --no-input
```

**Option 2: Using SSH Connection (If available with your database provider)**

Contact your database provider's support for SSH access instructions.

---

### **STEP 9: Create Superuser (Admin Account)**

Run this command locally with production database:

```bash
# Set DATABASE_URL to your production database
$env:DATABASE_URL = "postgresql://..." # Paste your Database URL

python manage.py createsuperuser
```

Or use Django shell:

```bash
$env:DATABASE_URL = "postgresql://..."
python manage.py shell

from django.contrib.auth.models import User
User.objects.create_superuser('admin', 'admin@gym.com', 'password123')
```

---

### **STEP 10: Test Your Deployment**

1. Open your Vercel domain in browser (e.g., https://barangay-gym-booking.vercel.app)
2. You should see your **Barangay Gym login page**
3. Try logging in with superuser credentials
4. Access admin at: `https://yourdomain.vercel.app/admin`

---

## ❌ TROUBLESHOOTING

### **Issue: "502 Bad Gateway" or "Internal Server Error"**

**Solution:**
```bash
# Check deployment logs in Vercel dashboard:
# 1. Project → Deployments (tab)
# 2. Click latest deployment
# 3. Scroll to "Build Logs" and "Runtime Logs"
# 4. Look for error messages
```

### **Issue: Static files not loading (CSS/JS broken)**

**Solution:** The `vercel.json` file triggers `collectstatic` automatically. If still broken:
```bash
vercel env pull
python manage.py collectstatic --noinput
git add .
git commit -m "Update static files"
git push
```

Then redeploy in Vercel dashboard.

### **Issue: Database migration fails**

**Solution:**
```bash
# Verify DATABASE_URL environment variable is correct
vercel env list

# Try migration locally with same database:
$env:DATABASE_URL = "your-production-db-url"
python manage.py migrate --noinput
```

### **Issue: Can't upload files or save bookings**

**Solution:** This is likely a **static files** or **permissions** issue. Try:
```bash
# Rebuild static files
python manage.py collectstatic --noinput --clear

# Then push to trigger Vercel rebuild
git add .
git commit -m "Fix static files"
git push
```

---

## 🔐 IMPORTANT SECURITY NOTES

1. **Never commit `.env` file to Git** - Use `.env.example` instead
2. **Always use strong passwords** for superuser/admin account
3. **In production, always keep `DEBUG = False`**
4. **Never share your `SECRET_KEY` or `DATABASE_URL`**
5. **Use HTTPS only** (Vercel provides free SSL certificates)

---

## 🔄 MAKING UPDATES AFTER DEPLOYMENT

Whenever you make changes locally:

```bash
# 1. Test locally
python manage.py runserver

# 2. Commit and push
git add .
git commit -m "Your change description"
git push origin main

# 3. Vercel auto-deploys! Check dashboard for status
```

---

## 📞 QUICK COMMANDS REFERENCE

```bash
# Test locally (after setting .env file)
python manage.py runserver

# Run migrations locally
python manage.py migrate

# Create new superuser locally
python manage.py createsuperuser

# Collect static files locally
python manage.py collectstatic --noinput

# Check Vercel deployment status
vercel status

# View production logs
vercel logs
```

---

## ✅ DEPLOYMENT CHECKLIST

- [ ] Git repository created and pushed to GitHub
- [ ] PostgreSQL database set up (Railway or Vercel Postgres)
- [ ] Vercel account created
- [ ] Project imported to Vercel
- [ ] All environment variables added in Vercel
- [ ] Deployment completed successfully
- [ ] Database migrations ran
- [ ] Superuser account created
- [ ] Login page loads without errors
- [ ] Admin panel accessible
- [ ] Bookings can be created and saved
- [ ] Static files (CSS/JS) load correctly

---

## 🎉 YOU'RE LIVE!

Your gym booking system is now live on the internet!

**Your Domain:** `https://barangay-gym-booking.vercel.app` (or custom domain)
**Admin Panel:** `https://yourdomain/admin`
**Login:** Use the superuser credentials you created

### Enjoy! 🎊
