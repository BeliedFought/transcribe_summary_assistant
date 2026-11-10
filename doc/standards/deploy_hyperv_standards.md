# Hyper-V Linux VM Deployment Standards. Version 5.0.1

Host-level OS overlay. Apply it together with `project_standards.md` and `web_standards.md` to deploy a Linux VM on a Windows host with Hyper-V. This document covers only the Windows/Hyper-V host level and initial guest OS setup; the web application is deployed on this VM per `web_standards.md`.

Target scenario - a Windows host with a Linux VM as a web server, with network access and standard backup. Scope - Windows 10/11 Pro or Enterprise, Windows Server 2016 and above; Hyper-V is unavailable on Windows Home. The document describes greenfield deployment; migration of an existing deployment is out of scope. Decision order when a rule is missing or ambiguous - `project_standards.md`, 07.06.

---

## Table of Contents

**01. General:** 01.01 Purpose and scope - 01.02 Host requirements - 01.03 Host readiness check - 01.04 Terms - 01.05 Agent autonomy boundaries

**02. Distribution and image source:** 02.01 Distribution choice - 02.02 Cloud image - 02.03 Download and verification - 02.04 qemu-img utility

**03. Disk layout and naming:** 03.01 Root and shared folders - 03.02 Virtual machine folder - 03.03 Naming rules - 03.04 Hyper-V path overrides - 03.05 Virtual machine passport

**04. Network:** 04.01 Access models - 04.02 Virtual switch - 04.03 Port forwarding through the host - 04.04 Guest own address - 04.05 Names and DNS - 04.06 Windows Firewall - 04.07 Connectivity check

**05. Image and media preparation:** 05.01 Image conversion to VHDX - 05.02 System disk extension - 05.03 Data disk - 05.04 CIDATA seed disk - 05.05 user-data template - 05.06 meta-data and network-config templates

**06. VM creation and start:** 06.01 VM creation - 06.02 Disk attachment - 06.03 Firmware and Secure Boot - 06.04 Memory and processors - 06.05 Power policy and autostart - 06.06 Checkpoints - 06.07 First start and login - 06.08 Seed disk removal

**07. Initial guest setup:** 07.01 Root filesystem extension - 07.02 User and SSH - 07.03 Time and locale - 07.04 OS updates - 07.05 Firewall and protection - 07.06 Data disk mount - 07.07 Data structure - 07.08 cloud-init completion

**08. Application level:** relation to `web_standards.md`

**09. Backup:** 09.01 Backup scope - 09.02 Policy - 09.03 Location and naming - 09.04 VM export and import - 09.05 Data export - 09.06 Integrity and rotation - 09.07 Restore verification

**10. Maintenance:** 10.01 Updates - 10.02 Scheduled maintenance - 10.03 Disks - 10.04 Monitoring - 10.05 Incidents - 10.06 VM migration

**11. Relations and versioning:** 11.01 Related documents - 11.02 Versioning

---

## 01. General

### 01.01. Purpose and scope

*Mandatory.*

- Host level: OS image preparation, Hyper-V VM creation, network, autostart, backup, maintenance; the application on the guest - `web_standards.md`. Mandatory for Linux VM deployment on a Windows host; does not apply to other deployment models.

### 01.02. Host requirements

*Mandatory.*

- Windows 10/11 Pro or Enterprise, or Windows Server 2016 and above (Hyper-V is unavailable on Home).
- CPU: 64-bit, SLAT, VT-x; hardware virtualization and DEP enabled in BIOS/UEFI.
- Memory: at least 4 GB for the host plus resources of all concurrently running VMs; free space for VMs, data disks and backups; administrator rights on the host (role, switch, firewall and port forwarding require elevation).

### 01.03. Host readiness check

*Mandatory.*

Run before any changes; record the results in the VM passport (03.05). In `systeminfo.exe`, all Hyper-V Requirements items must be Yes.

```powershell
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All | Select-Object FeatureName, State
Get-Command New-VM, Set-VM, New-VMSwitch -ErrorAction SilentlyContinue
Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{N='FreeGB';E={[math]::Round($_.Free/1GB,1)}}
# Install the role if missing; requires a host reboot (01.05)
Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All
```

### 01.04. Terms

*Mandatory.*

- **Host** - the physical Windows machine with the Hyper-V role. **Guest** - the Linux VM on the host. **Switch** - the Hyper-V virtual switch the VM is connected to.
- **Slug** - a short lowercase VM identifier, also the Hyper-V VM name and guest hostname.
- **Seed** - a medium with cloud-init data (`user-data`, `meta-data`) for initial guest setup. **VM passport** - a service document with actual VM parameters (03.05).

### 01.05. Agent autonomy boundaries

*Mandatory.*

- This document applies when the agent works on the Windows host directly (a PowerShell session with administrator rights). The base mode of `deploy_win_standards.md` (agent without direct access to the Windows machine) does not apply to these scenarios; there is no conflict - access modes differ.
- Points requiring explicit user confirmation: enabling the Hyper-V role and rebooting the host; creating or rebinding an external switch (may briefly interrupt host network); Windows Firewall and port forwarding changes; deleting VMs, disks, unregistering VMs; data operations (formatting the data disk, deleting backups).
- Secrets are not stored in the document or the VM folder: the private SSH key stays outside the VM folder, only the public key enters the seed; application passwords and tokens - in `.env` on the guest per `project_standards.md` (05.01).

---

## 02. Distribution and image source

### 02.01. Distribution choice

*Mandatory.*

- The canonical distribution is **Ubuntu Server 24.04 LTS** (Noble Numbat), amd64: official Hyper-V Generation 1/2 support (including Secure Boot), LIS drivers in the kernel, cloud images with cloud-init, long-term support. An acceptable alternative is 22.04 LTS; other distributions - by explicit user decision recorded in the VM passport.

### 02.02. Cloud image

*Mandatory.*

- Source - official cloud images at `https://cloud-images.ubuntu.com/releases/24.04/release/`; the main file is `ubuntu-24.04-server-cloudimg-amd64.img` (qcow2) with the same directory's `SHA256SUMS`. Hyper-V boots from VHDX, so the image is converted (05.01). The cloud image contains no credentials; login is possible only after initial setup via cloud-init (05.04-05.06).

### 02.03. Download and verification

*Mandatory.*

```powershell
$root = "D:\vms"; $baseUrl = "https://cloud-images.ubuntu.com/releases/24.04/release"; $image = "ubuntu-24.04-server-cloudimg-amd64.img"
New-Item -ItemType Directory -Force -Path "$root\iso" | Out-Null
Invoke-WebRequest "$baseUrl/$image"     -OutFile "$root\iso\$image"
Invoke-WebRequest "$baseUrl/SHA256SUMS" -OutFile "$root\iso\SHA256SUMS"
$expected = (Select-String -Path "$root\iso\SHA256SUMS" -Pattern $image).Line.Split()[0]
$actual = (Get-FileHash "$root\iso\$image" -Algorithm SHA256).Hash.ToLower()
if ($expected -ne $actual) { throw "SHA256 не совпала: образ поврежден или подменен" }
```

- Store the image and checksums in `<root>\iso\` and reuse them; when updating the image, do not delete the old version until the new VM deploys successfully.

### 02.04. qemu-img utility

*Mandatory.*

- Convert qcow2 to VHDX with `qemu-img`: `winget install --id SoftwareFreedomConservancy.QEMU -e --accept-source-agreements --accept-package-agreements` (alternatives: `https://qemu.weilnetz.de/w64/`, `choco install qemu`, `scoop install qemu`); default path - `C:\Program Files\qemu\qemu-img.exe`, add it to `PATH` when needed. The utility is needed only for conversion; all other operations use native Hyper-V tools.

---

## 03. Disk layout and naming

### 03.01. Root and shared folders

*Mandatory.*

All service data lives under one root `<root>` (default `D:\vms`), with no spaces in paths.

```
<root>\
  iso\            OS images and checksums
  tools\          qemu-img and helper utilities
  scripts\        deployment and backup PowerShell scripts
  logs\           operation logs by date
  backup\<slug>\  vm\<stamp>\ - full VM image; data\<stamp>\ - data dumps; seed\<stamp>\ - seed copies (09)
  <slug>\         folder of a specific VM (03.02)
```

### 03.02. Virtual machine folder

*Mandatory.*

VM configuration, disks, checkpoints and service data live only inside `<root>\<slug>\`, not in the default `C:\ProgramData` paths.

```
<root>\<slug>\
  config\        VM configuration (.vmcx, .vmgs)   <- New-VM -Path
  disks\         ext4.vhdx (system), data.vhdx (data)
  snapshots\     checkpoints (.avhdx, .vmrs)        <- Set-VM -SnapshotFileLocation
  smartpaging\   Smart Paging                      <- Set-VM -SmartPagingFilePath
  seed\          user-data, meta-data, seed.vhdx
  notes\         vm.md - VM passport (03.05)
```

### 03.03. Naming rules

*Mandatory.*

- Names and paths - Latin, lowercase, kebab-case, no spaces. Slug - `<role>-<nn>` (for example `srv-web-01`) or the project name in kebab-case; the slug sets the Hyper-V VM name and the guest hostname.
- Switch - `vsw-lan`; disks - `ext4.vhdx` (system) and `data.vhdx` (data); seed - `seed.vhdx`; seed volume label - `cidata` (05.04). Archive timestamps - `YYYYMMDD_HHMMSS`.

### 03.04. Hyper-V path overrides

*Mandatory.*

- Set the configuration folder at creation (`New-VM -Path`), the checkpoint folder before the first checkpoint (`Set-VM -SnapshotFileLocation`), and Smart Paging immediately (`Set-VM -SmartPagingFilePath`); create the `snapshots` and `smartpaging` directories in advance. Default paths for new VMs on the host: `Set-VMHost -VirtualMachinePath <root> -VirtualHardDiskPath <root>\<slug>\disks`; changing shared host paths is at the user's discretion.

### 03.05. Virtual machine passport

*Mandatory.*

`<root>\<slug>\notes\vm.md` - actual VM parameters; fill it during deployment and update it on changes. Minimum content: slug, VM name, hostname; Windows edition and Ubuntu version; switch, MAC, IP, access model (04.01); vCPU, memory, disk sizes; guest user and public key; data disk and mount point; published ports and forwarding/firewall rules; backup schedule and location, restore verification date; seed removal date, notes.

---

## 04. Network

### 04.01. Access models

*Mandatory.*

- **Model A (default). Forwarding through the host:** the VM gets its own address on the host network, port forwarding is configured on the host (04.03), clients connect to the host address and port; the VM address is pinned (04.04).
- **Model B. Direct access:** clients connect directly to the VM address; no port forwarding is configured. Record the model choice in the VM passport; the VM address cannot equal the host address - address conflict.

### 04.02. Virtual switch

*Mandatory.*

```powershell
New-VMSwitch -Name "vsw-lan" -NetAdapterName "Ethernet" -AllowManagementOS $true
Get-VMSwitch -Name "vsw-lan" | Select-Object Name, SwitchType, NetAdapterInterfaceDescription
```

- The external switch binds to the host physical adapter (name determined on site); `-AllowManagementOS $true` keeps network for the host (a service `vEthernet (vsw-lan)` adapter may appear). Create it once and reuse it for all VMs on the host.

### 04.03. Port forwarding through the host

*Mandatory under model A.*

- Forwarding uses `netsh interface portproxy`, TCP only; the VM address must be pinned (04.04), otherwise forwarding stops working after an address change. The external listen address is the host LAN address (preferred) or `0.0.0.0` (deliberate decision, firewall-controlled). The `iphlpsvc` (IP Helper) service must run with automatic start.

```powershell
$hostIp = "192.168.1.10"   # host LAN address
$vmIp = "192.168.1.50"     # VM address from 04.04
foreach ($p in 80, 443) { netsh interface portproxy add v4tov4 listenaddress=$hostIp listenport=$p connectaddress=$vmIp connectport=$p }
netsh interface portproxy show v4tov4
```

- Rules persist across reboots; update them when the VM address changes. Delete: `netsh interface portproxy delete v4tov4 listenaddress=<host-lan-ip> listenport=<port>`.

### 04.04. Guest own address

*Mandatory.*

- Default - DHCP from the host network; pin the address with a MAC-based reservation on the router. Set a static address via cloud-init (05.06) or netplan inside the guest; match the interface by name pattern:

```yaml
# netplan fragment (version 2), static address
network:
  version: 2
  ethernets:
    primary:
      match:
        name: "e*"
      addresses: [192.168.1.50/24]
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [192.168.1.1]
```

### 04.05. Names and DNS

*Mandatory.*

- The guest hostname matches the slug; for model A client names point to the host address, for model B to the VM address. Without local DNS, resolve the name through the client hosts file; record entries in the VM passport.

### 04.06. Windows Firewall

*Mandatory.*

- Traffic to the VM through the external switch is filtered by the host Windows Firewall; the default policy denies inbound. For model A open the published ports:

```powershell
New-NetFirewallRule -DisplayName "srv-web-01 http"  -Direction Inbound -Protocol TCP -LocalPort 80  -Action Allow
New-NetFirewallRule -DisplayName "srv-web-01 https" -Direction Inbound -Protocol TCP -LocalPort 443 -Action Allow
```

### 04.07. Connectivity check

*Mandatory.*

- VM address: `Get-VMNetworkAdapter -VMName "<slug>" | Select-Object -ExpandProperty IPAddresses`. Ports: `Test-NetConnection -ComputerName <vm-ip> -Port 22`; for model A also `Test-NetConnection -ComputerName <host-lan-ip> -Port 80`.

---

## 05. Image and media preparation

### 05.01. Image conversion to VHDX

*Mandatory.*

```powershell
$root = "D:\vms"; $slug = "srv-web-01"
$image = "$root\iso\ubuntu-24.04-server-cloudimg-amd64.img"
$disk = "$root\$slug\disks\ext4.vhdx"
New-Item -ItemType Directory -Force -Path "$root\$slug\disks" | Out-Null
qemu-img convert -p -f qcow2 -O vhdx -o subformat=dynamic,block_size=1M $image $disk
```

- VHDX format, `dynamic` subformat, `1M` block size; do not disable `block_state_zero`. The cloud image is unchanged - conversion creates a working VM copy.

### 05.02. System disk extension

*Mandatory.*

- Run before the first VM start while the disk is unused: `Resize-VHD -Path "$root\$slug\disks\ext4.vhdx" -SizeBytes 64GB` (default 64 GB; alternative - `qemu-img resize <image> 64G` before conversion, do not run both). For Generation 2 (SCSI), VHDX extension is allowed while the VM runs but not with an active checkpoint chain (10.03); the partition and filesystem inside the guest grow separately (07.01) - usually cloud-init handles this (`growpart`).

### 05.03. Data disk

*Mandatory.*

- Application and database data live on a separate `data.vhdx`; the system disk remains recreatable. Default size - 64 GB, type - dynamic.

```powershell
New-VHD -Path "$root\$slug\disks\data.vhdx" -SizeBytes 64GB -Dynamic -BlockSizeBytes 1MB
New-Item -ItemType Directory -Force -Path "$root\$slug\snapshots", "$root\$slug\smartpaging" | Out-Null   # folders in advance (03.04)
```

### 05.04. CIDATA seed disk

*Mandatory.*

The seed is the medium from which cloud-init obtains initial configuration: a small VHDX with FAT32 and volume label `cidata`, containing `user-data` and `meta-data` in the root.

```powershell
$seed = "$root\$slug\seed\seed.vhdx"
New-Item -ItemType Directory -Force -Path "$root\$slug\seed" | Out-Null
New-VHD -Path $seed -SizeBytes 64MB -Dynamic
$vhd = Mount-VHD -Path $seed -Passthru
$disk = Get-Disk -Number $vhd.DiskNumber
Initialize-Disk -Number $disk.Number -PartitionStyle MBR
$part = New-Partition -DiskNumber $disk.Number -UseMaximumSize -DriveLetter S
Format-Volume -Partition $part -FileSystem FAT32 -NewFileSystemLabel "cidata" -Confirm:$false
Copy-Item "$root\$slug\seed\user-data"      "S:\user-data"
Copy-Item "$root\$slug\seed\meta-data"      "S:\meta-data"
Copy-Item "$root\$slug\seed\network-config" "S:\network-config"
Dismount-VHD -Path $seed
```

- Mandatory files - `user-data` and `meta-data`; `network-config` is added for networking (05.06). Write files in UTF-8 without BOM, LF line endings, strictly in the volume root; an ISO9660 medium with the same label is acceptable. Keep the sources in `<root>\<slug>\seed\`; they are included in backups.

### 05.05. user-data template

*Mandatory.*

```yaml
#cloud-config
hostname: srv-web-01
manage_etc_hosts: true
users:
  - name: deploy
    groups: [adm, sudo]
    sudo: "ALL=(ALL) NOPASSWD:ALL"
    shell: /bin/bash
    lock_passwd: true
    ssh_authorized_keys:
      - ssh-ed25519 <ssh-public-key> admin
ssh_pwauth: false
disable_root: true
package_update: true
packages:
  - unattended-upgrades
growpart:
  mode: auto
  devices: ["/"]
resize_rootfs: true
```

- `<ssh-public-key>` - the administrator public key; the private key never enters the seed (01.05). `lock_passwd` and `ssh_pwauth: false` exclude password login. User `deploy` is the default name, recorded in the VM passport. Select packages for the application; the web runtime and nginx are installed at step 08 per `web_standards.md`.

### 05.06. meta-data and network-config templates

*Mandatory.*

- `meta-data`: `instance-id: srv-web-01`, `local-hostname: srv-web-01`. Networking is set by a separate `network-config` file: cloud-init does not apply network parameters from `user-data`; with DHCP do not describe the network separately. For a static address match the interface by MAC address, do not hardcode the name (predictable names are not guaranteed); take the MAC from `Get-VMNetworkAdapter -VMName <slug>` and record it in the VM passport:

```yaml
version: 2
ethernets:
  primary:
    match:
      macaddress: "00:15:5d:xx:xx:xx"
    set-name: eth0
    dhcp4: false
    addresses: [192.168.1.50/24]
    routes:
      - to: default
        via: 192.168.1.1
    nameservers:
      addresses: [192.168.1.1]
```

- Changes to `user-data` or `network-config` without an `instance-id` change are not applied: change `instance-id` or run `cloud-init clean`. Do not rerun the same seed after setup completes (06.08).

---

## 06. VM creation and start

### 06.01. VM creation

*Mandatory.*

```powershell
$root = "D:\vms"; $slug = "srv-web-01"

New-VM -Name $slug -Generation 2 -MemoryStartupBytes 8GB `
    -VHDPath "$root\$slug\disks\ext4.vhdx" -SwitchName "vsw-lan" -Path "$root\$slug\config"
# Service paths - immediately, before the first checkpoint (03.04)
Set-VM -Name $slug -SnapshotFileLocation "$root\$slug\snapshots" -SmartPagingFilePath "$root\$slug\smartpaging"
```

- Generation 2 (UEFI, Secure Boot, SCSI VHDX, online extension); the configuration folder is inside the VM folder (03.04).

### 06.02. Disk attachment

*Mandatory.*

```powershell
Add-VMHardDiskDrive -VMName $slug -Path "$root\$slug\disks\data.vhdx"
Add-VMHardDiskDrive -VMName $slug -Path "$root\$slug\seed\seed.vhdx"
# Set the first boot disk explicitly, otherwise Gen2 may boot from the network
$osDisk = Get-VMHardDiskDrive -VMName $slug | Where-Object Path -like "*ext4.vhdx"
Set-VMFirmware -VMName $slug -FirstBootDevice $osDisk
```

- Attachment order: system disk, data disk, seed. Remove the seed disk after initial setup completes (06.08).

### 06.03. Firmware and Secure Boot

*Mandatory.*

- For Generation 2 Linux use the Microsoft UEFI Certificate Authority template: `Set-VMFirmware -VMName $slug -SecureBootTemplate "MicrosoftUEFICertificateAuthority"`. If the guest does not boot, temporarily disable Secure Boot (`-EnableSecureBoot Off`) and record the change in the VM passport.
- With empty NVRAM boot follows the fallback path `\EFI\BOOT\BOOTX64.EFI`; if the system disk does not boot, create the fallback loader in the guest: copy `/boot/efi/EFI/ubuntu` to `/boot/efi/EFI/BOOT`, rename `shimx64.efi` to `BOOTX64.EFI` and `grub.cfg` to `BOOTX64.CFG`. Verify on the specific image.

### 06.04. Memory and processors

*Mandatory.*

- `Set-VM -Name $slug -ProcessorCount 4 -StaticMemory`; use fixed memory by default (predictable behavior under load), do not use dynamic memory for a server. Default limits: 4 vCPU, 8 GB memory, 64 GB system disk, 64 GB data disk; values come from the user decision and are recorded in the VM passport.

### 06.05. Power policy and autostart

*Mandatory.*

```powershell
Set-VM -Name $slug `
    -AutomaticStartAction Start -AutomaticStartDelay 30 `
    -AutomaticStopAction ShutDown -AutomaticCriticalErrorAction Pause -AutomaticCriticalErrorActionTimeout 30
```

- `Start` - autostart on host boot with a delay in seconds for service startup; `ShutDown` - graceful guest shutdown on host power-off; the critical error timeout is in minutes until the VM pauses. Control: `Start-VM`, `Stop-VM`, `Restart-VM`.

### 06.06. Checkpoints

*Mandatory.*

- `Set-VM -Name $slug -AutomaticCheckpointsEnabled $false -CheckpointType Production`: automatic checkpoints disabled, type Production (data-consistent, no memory snapshot). A checkpoint is a rollback point before risky changes, not a backup (09); stored in `<root>\<slug>\snapshots\` (03.04).

### 06.07. First start and login

*Mandatory.*

```powershell
Start-VM -Name $slug
# Wait for the address (poll the VM adapter), then log in with the administrator key
$vmIp = (Get-VMNetworkAdapter -VMName $slug).IPAddresses | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' } | Select-Object -First 1
ssh deploy@$vmIp
```

- On the guest verify cloud-init completion: `cloud-init status --wait`, `hostnamectl`, `ip -brief address`.
- Address waiting is bounded: poll the adapter with a pause for at most 10 minutes total; on timeout diagnose VM networking (04) and the seed (05); an endless wait loop is not allowed.

### 06.08. Seed disk removal

*Mandatory.*

- After cloud-init completes successfully and login is verified, remove the seed disk (prevents re-initialization); record the removal date in the VM passport. Never reattach the same seed to a running VM; keep the file and sources in `seed\` for history and backup:

```powershell
Get-VMHardDiskDrive -VMName $slug | Where-Object Path -like "*seed.vhdx" | Remove-VMHardDiskDrive
```

---

## 07. Initial guest setup

### 07.01. Root filesystem extension

*Optional - when cloud-init did not run growpart.*

- `sudo growpart /dev/sda 1 && sudo resize2fs /dev/sda1`; determine the device and partition with `lsblk` (the example shows typical layout), verify with `df -h /`.

### 07.02. User and SSH

*Mandatory.*

- cloud-init creates the user (05.05): groups `adm`, `sudo`, passwordless sudo, key-only login; the private key stays with the administrator only. Verify: `sudo sshd -T | grep -Ei 'passwordauthentication|permitrootlogin|pubkeyauthentication'`; expect password and root login disabled, key login enabled; apply changes with `sudo systemctl reload ssh`.

### 07.03. Time and locale

*Mandatory.*

- `sudo timedatectl set-timezone <timezone>`, verify with `timedatectl`, `locale`. Hyper-V provides time synchronization; additionally check the guest time service. Record timezone and locale in the VM passport.

### 07.04. OS updates

*Mandatory.*

- `sudo apt update && sudo apt upgrade -y`; automatic security updates - `unattended-upgrades` (`sudo dpkg-reconfigure -plow unattended-upgrades`). Reboot after a kernel update in the maintenance window (10.02).

### 07.05. Firewall and protection

*Mandatory for model B (direct access); for model A (host forwarding) - recommended as a second barrier.*

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from <admin-subnet>/24 to any port 22 proto tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

SSH is open only to the administration subnet (`<admin-subnet>` - the actual subnet from 04); the `allow OpenSSH` variant (port 22 from anywhere) is allowed only by explicit user decision.

- Open only required ports; port 22 from the trusted subnet; format rules with a comment, coordinate the set with `web_standards.md` (09.01). Additionally install `fail2ban` for SSH protection. For model A the guest firewall is a second barrier, not mandatory.

### 07.06. Data disk mount

*Mandatory.*

- Format the data disk as ext4 and mount it at `/srv/<slug>`; determine the device by size, not by name (`sda`/`sdb` may differ):

```bash
lsblk -o NAME,SIZE,FSTYPE
sudo mkfs.ext4 /dev/sdb   # example: /dev/sdb is the data disk
sudo mkdir -p /srv/<slug>
echo "UUID=$(sudo blkid -s UUID -o value /dev/sdb) /srv/<slug> ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
sudo mount -a && sudo chown deploy:deploy /srv/<slug> && df -h /srv/<slug>
```

### 07.07. Data structure

*Mandatory.*

- Application and database data live on the data disk at `/srv/<slug>`; the system disk is not used for application data (the VM remains recreatable without data loss). Data classes (`var/user`, `var/system`) and backup rules - per `web_standards.md` (02.07).

### 07.08. cloud-init completion

*Optional.*

- After seed disk removal, re-initialization does not occur; disable unneeded cloud-init with `sudo touch /etc/cloud/cloud-init.disabled` (record it in the VM passport). Reapply changed `user-data` or `network-config` only with an `instance-id` change or `sudo cloud-init clean --logs` followed by a reboot.

---

## 08. Application level

*Mandatory.* The guest application level is governed entirely by `web_standards.md`; this document does not duplicate it:

| Topic | Canon |
|-------|-------|
| Deployment model: A (systemd and nginx) or B (Docker compose), one model per node | `web_standards.md`, 01.04 |
| Application placement, system user, systemd units | `web_standards.md`, 05.01, 05.02 |
| nginx, TLS (ACME/certbot for a public domain, self-signed for LAN), update and rollback | `web_standards.md`, 07, 08, 10 |
| Application data on the data disk `/srv/<slug>` (07.06, 07.07); external publication - forward 80/443 through the host (04.03) | this document |

---

## 09. Backup

### 09.01. Backup scope

*Mandatory.*

- Full VM image (configuration and system disk) - whole-node recovery; data disk or application dumps - point-in-time data recovery; seed files and VM passport - reproducibility. Application files and configuration - per `web_standards.md` (10.01).

### 09.02. Policy

*Mandatory.*

- Default - daily: data export and full VM image; exact values come from the user decision and are recorded in the VM passport. Create an additional checkpoint before every configuration change (06.06). Retention: at least 7 daily copies; 4 weekly copies when space allows.

### 09.03. Location and naming

*Mandatory.*

- Backups live on a host disk separate from the VM, in `<root>\backup\<slug>\`; not on the disk holding working VM VHDX files. Naming: `vm\<YYYYMMDD_HHMMSS>\`, `data\<YYYYMMDD_HHMMSS>\`, `seed\<YYYYMMDD_HHMMSS>\`.

### 09.04. VM export and import

*Mandatory.*

Export a running VM through a Production checkpoint (consistent state):

```powershell
$slug = "srv-web-01"; $stamp = Get-Date -Format "yyyyMMdd_HHmmss"; $dest = "D:\vms\backup\$slug\vm\$stamp"
$cp = Checkpoint-VM -Name $slug -PassThru
Export-VM -Name $slug -Path $dest
$cp | Remove-VMCheckpoint
```

Delete only the checkpoint created for export (`-PassThru` returns its object); bulk deletion of all VM checkpoints is forbidden - working rollback points may be among them.

Restore (to a test or new VM): `Import-VM -Path "<dest>\<slug>\Virtual Machines\<GUID>.vmcx" -Copy -GenerateNewId` - registers a copy with a new identifier and leaves the backup directory untouched (`-Register` in place - only for target migration, not for backup verification).

### 09.05. Data export

*Mandatory.*

- Application and database dumps are produced by the application itself (`pg_dump`, SQLite backup), stored on the data disk, then copied to `<root>\backup\<slug>\data\<stamp>\`. DBMS consistency comes from the dump, not from copying files of a running database.

### 09.06. Integrity and rotation

*Mandatory.*

- After each copy verify archive presence and size (checksum for critical copies); rotation - delete copies older than the policy (09.02) while controlling free space; log backup failures in `<root>\logs\` and never ignore them.

### 09.07. Restore verification

*Mandatory.*

- At least quarterly, test-restore the VM image and data into an isolated environment and verify application operation; record the result (date, scope, outcome) in the VM passport. A backup without verified restore is considered non-working.

---

## 10. Maintenance

### 10.01. Updates

*Mandatory.*

- Host: Windows updates including Hyper-V, with a planned reboot; guest: `apt update && apt upgrade`, security updates automatically (07.04). Guest and host kernel updates - in the maintenance window (10.02). Linux integration drivers are part of the guest kernel; separate LIS installation is not required; verify with `lsmod | grep hv_`, `systemctl status hv-kvp-daemon`.

### 10.02. Scheduled maintenance

*Mandatory.*

- Order: stop the application in the guest, then `Stop-VM` (graceful shutdown), then host work; return with `Start-VM` and verify autostart and service availability.
- Rebooting the host with a running VM is a standard scenario: the VM must start automatically (06.05).

### 10.03. Disks

*Mandatory.*

- Dynamic VHDX files grow as data is written; monitor free space on the host disk and never let the data disk approach 100 percent - extend in advance. TRIM: periodically run `sudo fstrim -av` in the guest.
- Disk extension: remove the active checkpoint chain, then `Resize-VHD` and extend the partition and filesystem in the guest (`growpart`, `resize2fs`); VHDX extension is incompatible with an active checkpoint chain, VM shutdown is not mandatory (05.02) but guarantees the result when in doubt.
- Compress a dynamic VHDX only with the VM stopped, using native tools; before compression clean free space in the guest and run `fstrim`.

### 10.04. Monitoring

*Mandatory.*

- Host: `Get-VM`, Performance Monitor counters (Hyper-V Hypervisor, Virtual Processor, Virtual Network Adapter), event logs. Guest: free space (`df -h`), service state (`systemctl`), application logs.
- Minimum control: disk space on host and guest, VM state, service availability via health-check (`web_standards.md`, 10).

### 10.05. Incidents

*Mandatory.*

- Guest diagnostics: `journalctl`, `cloud-init status`, `systemctl --failed`; host: `Get-VM`, `Get-VMNetworkAdapter`, Hyper-V logs.
- Typical causes: VM does not start - Secure Boot, busy or corrupted VHDX (06.03); no network - switch rebind, address change (04.02, 04.04); forwarding broken - VM address changed, `iphlpsvc` stopped (04.03); host disk full - VHDX and backup growth (09.06, 10.03); guest filesystem errors - improper shutdown, check with a rescue ISO or `e2fsck` after attaching the disk to a separate Linux VM; repeated initial setup - seed not removed (06.08).

### 10.06. VM migration

*Mandatory.*

- Move to another disk or host by export and import (09.04) or native VM storage migration; after the move update the VM passport (paths, address, switch). For clustered VMs set a static MAC; a single host does not need it.

---

## 11. Relations and versioning

### 11.01. Related documents

| Document | Relation |
|----------|----------|
| `doc/standards/project_standards.md` | Core standard; this document applies on top of it (structure, security, documentation) |
| `doc/standards/web_standards.md` | Application level on the guest: deployment model (01.04), placement and systemd (05), nginx (07), TLS (08), update and rollback (10), data and backup (02.07) |
| `doc/standards/deploy_standards.md`, `deploy_lin_standards.md`, `deploy_win_standards.md` | Do not apply to web applications: their subject is CLI tool installation (boundary - `web_standards.md`, 12.02) |
| `doc/standards/deploy_docker_standards.md` | Applies to model B on the guest: compose, volumes, network, port publication |
| `doc/standards/_index_standards.md` | Package registry, routing map, versioning policy |

### 11.02. Versioning

Standards package versioning is unified for all package documents. The versioning policy, registry and routing map live in `doc/standards/_index_standards.md`. Bump the package version only on an explicit user request (see _index_standards.md).
