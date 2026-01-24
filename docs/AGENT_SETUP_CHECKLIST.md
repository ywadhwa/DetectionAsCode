# Self-Hosted Agent Setup Checklist

Since you're using the "Default" agent pool with a self-hosted agent (`DESKTOP-AKHLJNG`), ensure the following:

## ✅ Agent Status

**Current Status**: Your agent shows as "Offline" - it needs to be online to run pipelines.

### To Get Agent Online:

1. **Check Agent Service**
   - On `DESKTOP-AKHLJNG`, open **Services** (services.msc)
   - Find "Azure Pipelines Agent" service
   - Ensure it's **Running**
   - If not, start it

2. **Check Agent Configuration**
   - Navigate to agent installation directory (usually `C:\azp\agent` or similar)
   - Run: `.\config.cmd` to verify configuration
   - Or check if agent is running: `.\run.cmd`

3. **Verify Network Connection**
   - Agent must be able to reach Azure DevOps
   - Check firewall/proxy settings
   - Test connectivity to `dev.azure.com`

---

## ✅ Required Software on Agent

Your Windows agent (`DESKTOP-AKHLJNG`) needs these installed:

### 1. Python 3.11
- **Download**: https://www.python.org/downloads/
- **Install**: Python 3.11.x
- **Verify**: 
  ```powershell
  python --version
  # Should show: Python 3.11.x
  ```

### 2. Git
- **Download**: https://git-scm.com/download/win
- **Verify**:
  ```powershell
  git --version
  ```

### 3. Docker (for Splunk Testing)
- **Download**: https://www.docker.com/products/docker-desktop
- **Install**: Docker Desktop for Windows
- **Verify**:
  ```powershell
  docker --version
  docker-compose --version
  ```

### 4. PowerShell (usually pre-installed)
- **Verify**:
  ```powershell
  $PSVersionTable.PSVersion
  # Should be 5.1 or higher
  ```

---

## ✅ Agent Capabilities

The agent should have these capabilities configured:

1. **Agent.OS** = `Windows_NT` ✅ (Already configured in pipeline)
2. **Python** = `3.11` (optional, but helpful)
3. **Docker** = `true` (if using Splunk testing)

### To Add Capabilities:

1. In Azure DevOps: **Project Settings** → **Agent pools** → **Default** → **Agents** → **DESKTOP-AKHLJNG**
2. Click **Capabilities** tab
3. Add/edit capabilities as needed

---

## ✅ Agent Permissions

The agent needs permissions to:

1. **Read repository** (usually automatic)
2. **Write to file system** (for artifacts)
3. **Run Docker containers** (for Splunk testing)
4. **Access network** (for KQL testing, if used)

---

## ✅ Test Agent Connection

### From Azure DevOps:

1. Go to **Project Settings** → **Agent pools** → **Default**
2. Click on agent **DESKTOP-AKHLJNG**
3. Status should show **Online** (green)
4. Current status should be **Idle** or **Running**

### From Agent Machine:

1. Open PowerShell as Administrator
2. Navigate to agent directory
3. Check status:
   ```powershell
   .\run.cmd
   ```
4. You should see connection messages

---

## ✅ Pipeline Configuration

Your pipeline is already configured correctly:

```yaml
variables:
  agentPoolName: 'Default'  # ✅ Matches your pool
```

All stages use:
```yaml
pool:
  name: $(agentPoolName)  # ✅ Will use 'Default'
  demands:
    - Agent.OS -equals Windows_NT  # ✅ Requires Windows
```

---

## 🔧 Troubleshooting

### Agent Shows Offline

**Possible Causes:**
- Agent service not running
- Network connectivity issues
- Agent configuration expired
- Firewall blocking connection

**Solutions:**
1. Restart agent service
2. Reconfigure agent: `.\config.cmd remove` then `.\config.cmd`
3. Check firewall rules
4. Verify proxy settings (if behind proxy)

### Pipeline Queued but Not Running

**Possible Causes:**
- Agent offline
- Agent doesn't meet demands (Windows_NT)
- Agent busy with another job

**Solutions:**
1. Ensure agent is online
2. Check agent capabilities
3. Wait for agent to become available
4. Check agent logs

### Python Not Found

**Error**: `python: command not found`

**Solution**:
1. Install Python 3.11
2. Add Python to PATH during installation
3. Restart agent service
4. Verify: `python --version`

### Docker Not Available

**Error**: `docker: command not found` or `docker-compose: command not found`

**Solution**:
1. Install Docker Desktop
2. Ensure Docker service is running
3. Restart agent service
4. Verify: `docker ps`

---

## 📋 Quick Verification Script

Run this on your agent machine (`DESKTOP-AKHLJNG`) to verify everything:

```powershell
# Check Python
Write-Host "Python:" -NoNewline
python --version

# Check Git
Write-Host "Git:" -NoNewline
git --version

# Check Docker
Write-Host "Docker:" -NoNewline
docker --version

# Check Docker Compose
Write-Host "Docker Compose:" -NoNewline
docker-compose --version

# Check PowerShell
Write-Host "PowerShell:" -NoNewline
$PSVersionTable.PSVersion
```

All commands should succeed without errors.

---

## 🚀 Next Steps

Once your agent is online and has required software:

1. ✅ **Create the pipeline** in Azure DevOps
2. ✅ **Run a test pipeline** to verify agent works
3. ✅ **Monitor first run** to catch any issues
4. ✅ **Check agent logs** if problems occur

---

## 📝 Notes

- Agent must be **online** for pipelines to run
- Agent will show as **Idle** when waiting for jobs
- Agent will show as **Running** when executing a pipeline
- Multiple pipelines can queue if agent is busy
- Consider adding more agents if you have high pipeline volume
