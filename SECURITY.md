# 🔒 Security Guide

## ⚠️ CRITICAL: API Key Security

### **NEVER** commit API keys to Git!

This project uses environment variables to keep API keys secure. Follow these guidelines:

---

## 🚀 Quick Start (Secure Setup)

### 1. Create Your `.env` File

```bash
# Copy the example file
cp .env.example .env

# Edit with your API key
nano .env  # or use your favorite editor
```

### 2. Add Your API Key to `.env`

```bash
OPENAI_API_KEY=sk-your-actual-api-key-here
```

### 3. Verify `.env` is in `.gitignore`

```bash
# This should show .env in the list
cat .gitignore | grep .env
```

✅ The `.env` file is already in `.gitignore` and will **NOT** be committed to Git.

---

## 🔐 Environment Variables

### Required Variables

| Variable | Description | Where to Get It |
|----------|-------------|-----------------|
| `OPENAI_API_KEY` | OpenAI API key | [OpenAI Platform](https://platform.openai.com/api-keys) |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 5001 | Server port |
| `DEBUG` | False | Debug mode |

---

## 🛡️ Security Best Practices

### 1. **Never Hardcode API Keys**

❌ **WRONG:**
```python
OPENAI_API_KEY = "sk-1234567890..."  # DON'T DO THIS!
```

✅ **CORRECT:**
```python
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
```

### 2. **Use Different Keys for Development and Production**

- Development: Use a separate API key with lower rate limits
- Production: Use a dedicated production key
- Never share keys between environments

### 3. **Rotate Keys Regularly**

- Change your API keys every 90 days
- Immediately rotate if a key is exposed
- Use OpenAI's dashboard to manage keys

### 4. **Limit Key Permissions**

- Set usage limits in OpenAI dashboard
- Monitor usage regularly
- Set up billing alerts

### 5. **Secure Your `.env` File**

```bash
# Set restrictive permissions (Unix/Mac)
chmod 600 .env

# Verify it's in .gitignore
git check-ignore .env  # Should output: .env
```

---

## 🚨 If Your API Key is Exposed

### Immediate Actions:

1. **Revoke the compromised key immediately**
   - Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Delete the exposed key

2. **Generate a new key**
   - Create a new API key in the OpenAI dashboard
   - Update your `.env` file

3. **Check for unauthorized usage**
   - Review your OpenAI usage logs
   - Look for unusual API calls

4. **If committed to Git:**
   ```bash
   # Remove from Git history (careful!)
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   
   # Force push (if needed)
   git push origin --force --all
   ```

5. **Contact OpenAI support** if needed

---

## 📋 Pre-Commit Checklist

Before committing code, always check:

- [ ] No API keys in code files
- [ ] `.env` is in `.gitignore`
- [ ] No `.env` file is staged for commit
- [ ] All sensitive data uses environment variables
- [ ] `.env.example` has placeholder values only

### Automated Check

```bash
# Check if .env is staged (should return nothing)
git status | grep .env
```

---

## 🔍 Scanning for Exposed Secrets

### Using git-secrets (Recommended)

```bash
# Install git-secrets
brew install git-secrets  # Mac
# or: apt-get install git-secrets  # Linux

# Set up
git secrets --install
git secrets --register-aws

# Add custom patterns
git secrets --add 'sk-[a-zA-Z0-9]{48}'  # OpenAI keys

# Scan
git secrets --scan
```

### Manual Check

```bash
# Search for potential API keys
grep -r "sk-" . --exclude-dir=venv --exclude-dir=.git
grep -r "OPENAI_API_KEY.*=" . --exclude-dir=venv --exclude-dir=.git
```

---

## 🌐 Production Deployment

### For Cloud Deployment (Heroku, AWS, etc.)

**Never** use `.env` files in production. Instead:

#### Heroku
```bash
heroku config:set OPENAI_API_KEY=your-key-here
```

#### AWS Lambda
Use AWS Secrets Manager or environment variables

#### Docker
```bash
docker run -e OPENAI_API_KEY=your-key-here your-image
```

#### Kubernetes
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
type: Opaque
data:
  openai-api-key: <base64-encoded-key>
```

---

## 📞 Security Contacts

- **Report a security issue**: Create a private issue in the repository
- **OpenAI Security**: security@openai.com
- **Urgent API key exposure**: [OpenAI Dashboard](https://platform.openai.com/api-keys)

---

## 📚 Additional Resources

- [OpenAI API Best Practices](https://platform.openai.com/docs/guides/safety-best-practices)
- [OWASP API Security](https://owasp.org/www-project-api-security/)
- [12 Factor App - Config](https://12factor.net/config)

---

<div align="center">

**🔒 Security is everyone's responsibility**

Stay vigilant, keep your keys safe!

</div>

