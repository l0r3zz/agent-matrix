Script started on 2026-02-11 22:34:34-08:00 [TERM="xterm-256color" TTY="/dev/pts/13" COLUMNS="95" LINES="50"]
d2on41.353zz@tarnover:[2026-02-11 22:34:35]-$Bm#I'm starting the build of a new Kubernetes cluster base
?2004hl0r3zz@tarnover:[2026-02-11 22:35:05]-$Bmf1@#1@let's make sure the appropriate portKs are open
l0r3zz@tarnover:[2026-02-11C22:35:39]-$BmexitKartingstheebuildaof aunewtKubernetesiclustertbased one1.35A
KACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC1Pssh root@k8-0.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 07:36:02 CET 2026

  System load:		 0.06
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 124
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 07:21:58 2026 from 73.222.150.26
?2004hroot@k8-0:[2026-02-12 07:36:03]-#Bm#control plane node
?2004hroot@k8-0:[2026-02-12 07:36:13]-#Bm# open ports
?2004hroot@k8-0:[2026-02-12 07:36:27]-#Bm7msudo ufw allow 6443/tcp27m
7msudo ufw allow 2379:2380/tcp27m
7msudo ufw allow 10250/tcp27m
7msudo ufw allow 10259/tcp27m
7msudo ufw allow 10257/tcp27m
AAAAACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCsudo ufw allow 6443/tcp
sudo ufw allow 2379:2380/tcp
sudo ufw allow 10250/tcp
sudo ufw allow 10259/tcp
sudo ufw allow 10257/tcp
A
Ruleslupdated
Rules updated (v6)
Rules updated
Rules updated (v6)
Rules updated
Rules updated (v6)
Rules updated
Rules updated (v6)
Rules updated
Rules updated (v6)
?2004hroot@k8-0:[2026-02-12 07:36:41]-#Bm7msudo ufw enable27m
7msudo ufw status27m
AACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCsudo ufw enable
sudo ufw status
A
Command may disrupt existing ssh connections. Proceed with operation (y|n)? y
Firewall is active and enabled on system startup
Status: active

To			   Action      From
--			   ------      ----
6443/tcp		   ALLOW       Anywhere
2379:2380/tcp		   ALLOW       Anywhere
10250/tcp		   ALLOW       Anywhere
10259/tcp		   ALLOW       Anywhere
10257/tcp		   ALLOW       Anywhere
6443/tcp (v6)		   ALLOW       Anywhere (v6)
2379:2380/tcp (v6)	   ALLOW       Anywhere (v6)
10250/tcp (v6)		   ALLOW       Anywhere (v6)
10259/tcp (v6)		   ALLOW       Anywhere (v6)
10257/tcp (v6)		   ALLOW       Anywhere (v6)

?2004hroot@k8-0:[2026-02-12 07:37:07]-#Bmexit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-11 22:37:29]-$Bmssh root@k8-1P1.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 07:37:37 CET 2026

  System load:		 0.06
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 123
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 07:23:31 2026 from 73.222.150.26
Command 'kubectl' not found, but can be installed with:
snap install kubectl
?2004hroot@k8-1:[2026-02-12 07:37:38]-#Bm# worker node
?2004hroot@k8-1:[2026-02-12 07:37:48]-#Bm# Make sure ports are open
?2004hroot@k8-1:[2026-02-12 07:37:57]-#Bm7msudo ufw allow 10250/tcp27m
7msudo ufw allow 30000:32767/tcp27m
AACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCsudo ufw allow 10250/tcp
sudo ufw allow 30000:32767/tcp
A
Ruleslupdated
Rules updated (v6)
Rules updated
Rules updated (v6)
?2004hroot@k8-1:[2026-02-12 07:38:11]-#Bm7msudo ufw enable27m
7msudo ufw status27m
AACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCsudo ufw enable
sudo ufw status
A
Command may disrupt existing ssh connections. Proceed with operation (y|n)? y
Firewall is active and enabled on system startup
Status: active

To			   Action      From
--			   ------      ----
10250/tcp		   ALLOW       Anywhere
30000:32767/tcp		   ALLOW       Anywhere
10250/tcp (v6)		   ALLOW       Anywhere (v6)
30000:32767/tcp (v6)	   ALLOW       Anywhere (v6)

?2004hroot@k8-1:[2026-02-12 07:38:31]-#Bmexit
logout
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-11 22:38:38]-$Bmssh root@k8-1P2.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 07:38:51 CET 2026

  System load:		 0.08
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 125
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 07:28:38 2026 from 73.222.150.26
Command 'kubectl' not found, but can be installed with:
snap install kubectl
?2004hroot@k8-2:[2026-02-12 07:38:52]-#Bm# worker node
?2004hroot@k8-2:[2026-02-12 07:39:07]-#Bm# make sure k8 ports are open
?2004hroot@k8-2:[2026-02-12 07:39:20]-#Bm7msudo ufw allow 10250/tcp27m
7msudo ufw allow 30000:32767/tcp27m
AACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCsudo ufw allow 10250/tcp
sudo ufw allow 30000:32767/tcp
A
Ruleslupdated
Rules updated (v6)
Rules updated
Rules updated (v6)
?2004hroot@k8-2:[2026-02-12 07:39:31]-#Bm7msudo ufw enable27m
7msudo ufw status27m
AACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCsudo ufw enable
sudo ufw status
A
Command may disrupt existing ssh connections. Proceed with operation (y|n)? y
Firewall is active and enabled on system startup
Status: active

To			   Action      From
--			   ------      ----
10250/tcp		   ALLOW       Anywhere
30000:32767/tcp		   ALLOW       Anywhere
10250/tcp (v6)		   ALLOW       Anywhere (v6)
30000:32767/tcp (v6)	   ALLOW       Anywhere (v6)

?2004hroot@k8-2:[2026-02-12 07:39:43]-#Bmexit
logout
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-11 22:39:51]-$Bmssh root@k8-0.v-site.net
^C004l
?2004hl0r3zz@tarnover:[2026-02-11 22:41:33]-$Bmssh root@k8-2.v-site.net
^C004l
?2004hl0r3zz@tarnover:[2026-02-11 22:41:45]-$Bmssh root@k8-1.v-site.net
^C004l
orgothtoropentportv22::(026-02-11 22:41:54]-$Bm# looks like my fw changes locked myself out because I f
l0r3zz@tarnover:[2026-02-11-22:42:25]-$Bm32Pssh#root@k8-1.v-site.netanges locked myself out because I forgot to open port 22 :(A
?2004h?2004lCCCCCCCCCCCCCCCCCCCCCCCCCCCCI'mfstarting'theabuildroftaenewpKubernetesocluster based on 1.35^C?2004l
220ishenabledt:)nover:[2026-02-12 00:31:31]-$Bmhad to rebuildK# I had to rKebuild all the servers making sure that tcp/
l0r3zz@tarnover:[2026-02-12-00:32:10]-$Bm32Psshsroot@k8-1.v-site.netlockedsmyself outibecause Ihforgot/to opennportd22):(A
l0r3zz@tarnover:[2026-02-12C00:32:10]-$BmexitKarting'theabuildroftaenewpKubernetesocluster based on 1.35A
l0r3zz@tarnover:[2026-02-12C00:32:10]-$BmCCC32Pkroot@k8-0.v-site.netzz/.ssh/known_hosts" -R "k8-0.v-site.net"A
l0r3zz@tarnover:[2026-02-12C00:32:10]-$BmCCC32Pyroot@k8-0.v-site.net/.ssh/known_hosts" -R "k8-0.v-site.net"A
KACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCl/usr/bin/bashC--init-file /usr/share/windsurf/resources/app/out/vs/workbench/contrib/terminal/common/scripts/shellIntegratKon-bash.shA
?2004h?2004lCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCpioC15P15P15Prunn-tnupload^C?2004ltime
l0r3zz@tarnover:[2026-02-12-00:32:45]-$Bm32Psshsroot@k8-1.v-site.netlockedsmyself outibecause Ihforgot/to opennportd22):(A
KACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC0.v-site.net
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!	  @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the ED25519 key sent by the remote host is
SHA256:l23oXm758VoHi4No0CZ6rvxOzd3yz5k29IDaQem3N+o.
Please contact your system administrator.
Add correct host key in /home/l0r3zz/.ssh/known_hosts to get rid of this message.
Offending ED25519 key in /home/l0r3zz/.ssh/known_hosts:11
  remove with:
  ssh-keygen -f "/home/l0r3zz/.ssh/known_hosts" -R "k8-0.v-site.net"
Host key for k8-0.v-site.net has changed and you have requested strict checking.
Host key verification failed.
l0r3zz@tarnover:[2026-02-12-00:36:24]-$Bmssh-keygenh-fe"/home/l0r3zz/.ssh/known_hosts"n-Ro"k8-0.v-site.net"m7m-27m7msite.net"27mA
```bash
#2Host k8-0.v-site.net found: line 11
```
/home/l0r3zz/.ssh/known_hosts updated.
Original contents retained as /home/l0r3zz/.ssh/known_hosts.old
?2004hl0r3zz@tarnover:[2026-02-12 00:36:47]-$Bmssh-copy-id root@k8-0.v-site.net
The0authenticity of host 'k8-0.v-site.net (144.126.131.105)' can't be established.
ED25519 key fingerprint is SHA256:l23oXm758VoHi4No0CZ6rvxOzd3yz5k29IDaQem3N+o.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed
/usr/bin/ssh-copy-id: INFO: 8 key(s) remain to be installed -- if you are prompted now it is to install the new keys
root@k8-0.v-site.net's password:

Number of key(s) added: 8

Now try logging into the machine, with:	  "ssh 'root@k8-0.v-site.net'"
and check to make sure that only the key(s) you wanted were added.

l0r3zz@tarnover:[2026-02-12-00:38:17]-$BmCCC32Psroot@k8-0.v-site.netl0r3zz/.ssh/known_hosts" -R "k8-0.v-site.net"A
KACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:38:16 CET 2026

  System load:		 0.02
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 4%
  Swap usage:		 0%
  Processes:		 126
  Users logged in:	 1
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***
  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:30:55 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:38:33]-$Bmssh root@k8-1P1.v-site.net
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!	  @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
Someone could be eavesdropping on you right now (man-in-the-middle attack)!
It is also possible that a host key has just been changed.
The fingerprint for the ED25519 key sent by the remote host is
SHA256:gdNwtTbTOius/hACcHN1sAugLB79u/63lWikjlY0NLE.
Please contact your system administrator.
Add correct host key in /home/l0r3zz/.ssh/known_hosts to get rid of this message.
Offending ED25519 key in /home/l0r3zz/.ssh/known_hosts:9
  remove with:
  ssh-keygen -f "/home/l0r3zz/.ssh/known_hosts" -R "k8-1.v-site.net"
Host key for k8-1.v-site.net has changed and you have requested strict checking.
Host key verification failed.
l0r3zz@tarnover:[2026-02-12-00:38:49]-$Bmssh-keygenh-fe"/home/l0r3zz/.ssh/known_hosts"n-Ro"k8-1.v-site.net"m7m-27m7msite.net"27mA
```bash
#2Host k8-1.v-site.net found: line 9
```
/home/l0r3zz/.ssh/known_hosts updated.
Original contents retained as /home/l0r3zz/.ssh/known_hosts.old
l0r3zz@tarnover:[2026-02-12-00:39:07]-$BmCCC32Psroot@k8-1.v-site.netl0r3zz/.ssh/known_hosts" -R "k8-1.v-site.net"A
KACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
The0authenticity of host 'k8-1.v-site.net (207.244.225.169)' can't be established.
ED25519 key fingerprint is SHA256:gdNwtTbTOius/hACcHN1sAugLB79u/63lWikjlY0NLE.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added 'k8-1.v-site.net' (ED25519) to the list of known hosts.
root@k8-1.v-site.net's password:
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:39:37 CET 2026

  System load:		 0.13
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 123
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***

The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

?2004h0;root@vmi1146819: ~root@vmi1146819:~# exit
logout
Connection to k8-1.v-site.net closed.
l0r3zz@tarnover:[2026-02-12-00:39:57]-$BmCCC32Psroot@k8-1.v-site.netl0r3zz/.ssh/known_hosts" -R "k8-1.v-site.net"A
KACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC-copy-idrroot@k8-1.v-site.net
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed
/usr/bin/ssh-copy-id: INFO: 8 key(s) remain to be installed -- if you are prompted now it is to install the new keys
root@k8-1.v-site.net's password:

Number of key(s) added: 8

Now try logging into the machine, with:	  "ssh 'root@k8-1.v-site.net'"
and check to make sure that only the key(s) you wanted were added.

?2004hl0r3zz@tarnover:[2026-02-12 00:40:38]-$Bmssh8Poroot@k8-1.v-site.nette.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:40:46 CET 2026

  System load:		 0.1
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 128
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***
  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:39:39 2026 from 73.222.150.26
?2004h0;root@vmi1146819: ~root@vmi1146819:~# exit
logout
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:40:51]-$Bmssh-copy-id-root@k8-1P2.v-site.net
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed

/usr/bin/ssh-copy-id: ERROR: @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
ERROR: @    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!	 @
ERROR: @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
ERROR: IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
ERROR: Someone could be eavesdropping on you right now (man-in-the-middle attack)!
ERROR: It is also possible that a host key has just been changed.
ERROR: The fingerprint for the ED25519 key sent by the remote host is
ERROR: SHA256:QiYYwilvBNTJ9ZRkRIrK6h00NzoFNnxl71cdI9Jt6HA.
ERROR: Please contact your system administrator.
ERROR: Add correct host key in /home/l0r3zz/.ssh/known_hosts to get rid of this message.
ERROR: Offending ED25519 key in /home/l0r3zz/.ssh/known_hosts:9
ERROR:	 remove with:
ERROR:	 ssh-keygen -f "/home/l0r3zz/.ssh/known_hosts" -R "k8-2.v-site.net"
ERROR: Host key for k8-2.v-site.net has changed and you have requested strict checking.
ERROR: Host key verification failed.

l0r3zz@tarnover:[2026-02-12-00:41:06]-$Bmssh-keygenh-fe"/home/l0r3zz/.ssh/known_hosts"n-Ro"k8-2.v-site.net"m7m-27m7msite.net"27mA
```bash
#2Host k8-2.v-site.net found: line 9
```
/home/l0r3zz/.ssh/known_hosts updated.
Original contents retained as /home/l0r3zz/.ssh/known_hosts.old
l0r3zz@tarnover:[2026-02-12-00:41:23]-$BmCCCC24Pcopy-ideroot@k8-2.v-site.netssh/known_hosts" -R "k8-2.v-site.net"A
KACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
The0authenticity of host 'k8-2.v-site.net (207.244.237.219)' can't be established.
ED25519 key fingerprint is SHA256:QiYYwilvBNTJ9ZRkRIrK6h00NzoFNnxl71cdI9Jt6HA.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
/usr/bin/ssh-copy-id: INFO: attempting to log in with the new key(s), to filter out any that are already installed
/usr/bin/ssh-copy-id: INFO: 8 key(s) remain to be installed -- if you are prompted now it is to install the new keys
root@k8-2.v-site.net's password:

Number of key(s) added: 8

Now try logging into the machine, with:	  "ssh 'root@k8-2.v-site.net'"
and check to make sure that only the key(s) you wanted were added.

l0r3zz@tarnover:[2026-02-12-00:41:54]-$BmCCCC24Pcopy-ideroot@k8-2.v-site.netssh/known_hosts" -R "k8-2.v-site.net"A
l0r3zz@tarnover:[2026-02-12C00:41:54]-$BmCCCC24Pcopy-id"root@k8-2.v-site.netown_hosts" -R "k8-2.v-site.net"A
KACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC8PCroot@k8-1P2.v-site.netCCCC
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:41:53 CET 2026

  System load:		 0.0
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 125
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***
  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

?2004h0;root@vmi1159519: ~root@vmi1159519:~# exit
logout
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:42:14]-$Bmssh root@k8-1P0.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:42:27 CET 2026

  System load:		 0.0
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 129
  Users logged in:	 1
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***
  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:38:24 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:42:32]-$Bmssh root@k8-1P1.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:42:44 CET 2026

  System load:		 0.01
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 129
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***
  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:40:46 2026 from 73.222.150.26
?2004h0;root@vmi1146819: ~root@vmi1146819:~# hodtnamectlKostnamectl k8-1
0;1;31mUnknown command verb 'k8-1', did you mean 'help'?0m
?2004h0;root@vmi1146819: ~root@vmi1146819:~# hostnamectlCset-hostnamekk8-1
?2004h0;root@vmi1146819: ~root@vmi1146819:~# hostname
k8-14l
?2004h0;root@vmi1146819: ~root@vmi1146819:~# vi /etc/hosts
?1049h22;0;0t>4;2m?1h?2004h?1004h1;50r?12h?12l22;2t22;1t27m23m29mmH2J?25l50;1H"/etc/hosts" 15L, 565B2;1H▽6n2;1H	 3;1Hzz0%m6n3;1H	   1;1H>c10;?11;?1;1H34m# Your system has configured 'manage_etc_hosts' as True.
```bash
# As a result, if you wish for changes to this file to persistm2;63HK3;1H34m# then you will need to eitherm3;31HK4;1H34m# a.) make changes to the master file in /etc/cloud/templates/hosts.debian.tmpl
```
```bash
# b.) change or remove the value of 'manage_etc_hosts' in
```
```bash
#     /etc/cloud/cloud.cfg or cloud-config from user-data
```
```bash
#m
```
127.0.1.1 vmi1146819.contaboserver.net vmi1146819
127.0.0.1 localhost

34m# The following lines are desirable for IPv6 capable hostsm
::1 localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

94m~												  17;1H~											      18;1H~												  19;1H~											      20;1H~												  21;1H~											      22;1H~												  23;1H~											      24;1H~												  25;1H~											      26;1H~												  27;1H~											      28;1H~												  29;1H~											      30;1H~												  31;1H~											      32;1H~												  33;1H~											      34;1H~												  35;1H~											      36;1H~												  37;1H~											      38;1H~												  39;1H~											      40;1H~												  41;1H~											      42;1H~												  43;1H~											      44;1H~												  45;1H~											      46;1H~												  47;1H~											      48;1H~												  49;1H~											      m50;78H1,111CAll1;1H?25h?4m+q436f+q6b75+q6b64+q6b72+q6b6c+q2332+q2334+q2569+q2a37+q6b31$q q?12$p?25l50;68H:1;1H50;69H01;1H50;70H01;1H50;71H01;1H50;72H01;1H50;73H/1;1H50;74H01;1H50;75H01;1H50;76H01;1H50;77H01;1H50;68H		1;1H27m23m29mmH2J1;1H96m# Your system has configured 'manage_etc_hosts' as True.
```bash
# As a result, if you wish for changes to this file to persist
```
```bash
# then you will need to either
```
```bash
# a.) make changes to the master file in /etc/cloud/templates/hosts.debian.tmpl
```
```bash
# b.) change or remove the value of 'manage_etc_hosts' in
```
```bash
#     /etc/cloud/cloud.cfg or cloud-config from user-data
```
```bash
#m
```
127.0.1.1 vmi1146819.contaboserver.net vmi1146819
127.0.0.1 localhost

96m# The following lines are desirable for IPv6 capable hostsm
::1 localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

23;2t23;1t>4;m"/etc/hosts"?15L,2546B;written;1H50;68H	2;1H50;78H22;1H?25h?25l50;68H~@k2;1H50;68H17;3;1H50;78H33;1H?25h?25l50;68H~@k3;1H50;68H	  4;1H50;78H44;1H?25h?25l50;68H~@k4;1H50;68H   5;1H50;78H55;1H?25h?25l50;68H~@k5;1H50;68H   6;1H50;78H66;1H?25h?25l50;68H~@k6;1H50;68H	 7;1H50;78H77;1H?25h?25l50;68H~@k7;1H50;68H   8;1H50;78H88;1H?25h?25l50;68H~@k8;1H50;68H   8;2H50;80H28;2H?25h?25l50;68H~@k8;2H50;68H	8;3H50;80H38;3H?25h?25l50;68H~@k8;3H50;68H   8;4H50;80H48;4H?25h?25l50;68H~@k8;4H50;68H~  8;5H50;80H58;5H?25h?25l50;68H~@k8;5H50;68H   8;6H50;80H68;6H?25h?25l50;68H~@k8;6H50;68H   8;7H50;80H78;7H?25h?25l50;68H~@k8;7H50;68H	 8;8H50;80H88;8H?25h?25l50;68H~@k8;8H50;68H   8;9H50;80H98;9H?25h?25l50;68H~@k8;9H50;68H   8;10H50;80H108;10H?25h?25l50;68H~@k8;10H50;68H   8;11H50;81H18;11H?25h?25l50;68Hc8;11H?25h?25l50;69Hw8;11H50;68H  8;11H50;1H1m-- INSERT --m50;14HK50;78H8,1110CAll8;11H.contaboserver.net vmi11468198;40HK8;11H?25h?25lk.contaboserver.net vmi114681950;81H28;12H?25h?25l8.contaboserver.net vmi114681950;81H38;13H?25h?25l-.contaboserver.net vmi114681950;81H48;14H?25h?25l1.contaboserver.net vmi114681950;81H58;15H?25h50;1HK8;14H?25l50;68H^[8;14H50;68H  8;15H50;78H8,1410CAll8;14H?25h?25l50;68H~@k8;14H50;68H   8;15H50;81H58;15H?25h?25l50;68H~@k8;15H50;68H   8;16H50;81H68;16H?25h?25l50;68H~@k8;16H50;68H   8;17H50;81H78;17H?25h?25l50;68H~@k8;17H50;68H   8;18H50;81H88;18H?25h?25l50;68H~@k8;18H50;68H   8;19H50;81H98;19H?25h?25l50;68H~@k8;19H50;68H   8;20H50;80H208;20H?25h?25l50;68H~@k8;20H50;68H   8;21H50;81H18;21H?25h?25l50;68H~@k8;21H50;68H   8;22H50;81H28;22H?25h?25l50;68H~@k8;22H50;68H   8;23H50;81H38;23H?25h?25l50;68H~@k8;23H50;68H   8;24H50;81H48;24H?25h?25l50;68H~@k8;24H50;68H   8;25H50;81H58;25H?25h?25l50;68H~@k8;25H50;68H   8;26H50;81H68;26H?25h?25l50;68H~@k8;26H50;68H   8;27H50;81H78;27H?25h?25l50;68H~@k8;27H50;68H   8;28H50;81H88;28H?25h?25l50;68H~@k8;28H50;68H   8;29H50;81H98;29H?25h?25l50;68H~@k8;29H50;68H   8;30H50;80H308;30H?25h?25l50;68H~@k8;30H50;68HH~ 8;31H50;81H18;31H?25h?25l50;68H~@k8;31H50;68H   8;32H50;81H28;32H?25h?25l50;68H~@k8;32H50;68H37;8;33H50;81H38;33H?25h?25l50;68H~@k8;33H50;68H   8;34H50;81H48;34H?25h?25l50;68H.8;34H50;68H 8;34H50;1H1m-- INSERT --m50;78HK50;78H8,3410CAll50;1HK8;34Hk8-8;38HK50;78H8,3710CAll8;37H?25h?25l50;68H~@k8;37H50;68H	 8;36H50;81H68;36H?25h?25l50;68H~@k8;36H50;68H	 8;35H50;81H58;35H?25h?25l50;68H~@k8;35H50;68H	 8;34H50;81H48;34H?25h?25l50;68H~@k8;34H50;68H	 8;33H50;81H38;33H?25h?25l50;68H~@k8;33H50;68HH~ 8;32H50;81H28;32H?25h?25l50;68H~@k8;32H50;68H	 8;31H50;81H18;31H?25h?25l50;68H~@k8;31H50;68H42;8;30H50;81H08;30H?25h?25l50;68H~@k8;30H50;68H	 8;29H50;80H298;29H?25h?25l50;68H~@k8;29H50;68H	  8;28H50;81H88;28H?25h?25l50;68H~@k8;28H50;68H	  8;27H50;81H78;27H?25h?25l50;68H~@k8;27H50;68H	  8;26H50;81H68;26H?25h?25l50;68H~@k8;26H50;68H	  8;25H50;81H58;25H?25h?25l50;68H~@k8;25H50;68H	  8;24H50;81H48;24H?25h?25l50;68H~@k8;24H50;68H	  8;23H50;81H38;23H?25h?25l50;68H~@k8;23H50;68H	  8;22H50;81H28;22H?25h?25l50;68H~@k8;22H50;68H	  8;21H50;81H18;21H?25h?25l50;68H~@k8;21H50;68H	  8;20H50;81H08;20H?25h?25l50;68H~@k8;20H50;68H	  8;19H50;80H198;19H?25h?25l50;68H~@k8;19H50;68H   8;18H50;81H88;18H?25h?25l50;68H~@k8;18H50;68H   8;17H50;81H78;17H?25h?25l50;68H~@k8;17H50;68H   8;16H50;81H68;16H?25h?25l50;68Hc8;16H?25h?25l50;69Hw8;16H50;68H  8;16H50;1H1m-- INSERT --m50;78HK50;78H8,1610CAll8;16H.net k8-18;25HK8;16H?25h?25lv.net k8-150;81H78;17H?25h?25l-.net k8-150;81H88;18H?25h?25ls.net k8-150;81H98;19H?25h?25li.net k8-150;80H208;20H?25h?25lt.net k8-150;81H18;21H?25h?25le.net k8-150;81H28;22H?25h50;1HK8;21H?25l50;68H^[8;21H50;68H  8;22H50;78H8,2110CAll8;21H?25h?25l50;68H^[8;21H50;68H	 8;21H50;68H^[8;21H50;68H  8;21H?25h?25l50;68H:8;21H50;68HK50;1H:?25hwq
?1004l?2004l?1l?1049l23;0;0t?25h>4;m?2004h0;root@vmi1146819: ~root@vmi1146819:~# hostname
k8-14l
?2004h0;root@vmi1146819: ~root@vmi1146819:~# 7msudo ufw allow 10250/tcp27m
7msudo ufw allow 30000:32sudotufw7allow 10250/tcp
sudo ufw allow 30000:32767/tcp
Ruleslupdated
Rules updated (v6)
Rules updated
Rules updated (v6)
?2004h0;root@vmi1146819: ~root@vmi1146819:~# sudo ufw allow 22/tcp
Ruleslupdated
Rules updated (v6)
?2004h0;root@vmi1146819: ~root@vmi1146819:~# ufw status
Status: inactive
?2004h0;root@vmi1146819: ~root@vmi1146819:~# ufw list
ERROR: Invalid syntax

Usage: ufw COMMAND

Commands:
 enable				 enables the firewall
 disable			 disables the firewall
 default ARG			 set default policy
 logging LEVEL			 set logging to LEVEL
 allow ARGS			 add allow rule
 deny ARGS			 add deny rule
 reject ARGS			 add reject rule
 limit ARGS			 add limit rule
 delete RULE|NUM		 delete RULE
 insert NUM RULE		 insert RULE at NUM
 prepend RULE			 prepend RULE
 route RULE			 add route RULE
 route delete RULE|NUM		 delete route RULE
 route insert NUM RULE		 insert route RULE at NUM
 reload				 reload firewall
 reset				 reset firewall
 status				 show firewall status
 status numbered		 show firewall status as numbered list of RULES
 status verbose			 show verbose firewall status
 show ARG			 show firewall report
 version			 display version information

Application profile commands:
 app list			 list application profiles
 app info PROFILE		 show information on PROFILE
 app update PROFILE		 update PROFILE
 app default ARG		 set default application policy

?2004h0;root@vmi1146819: ~root@vmi1146819:~# ufw lisKstatus numbered
Status: inactive
?2004h0;root@vmi1146819: ~root@vmi1146819:~# ufw enableK
Command may disrupt existing ssh connections. Proceed with operation (y|n)? y
Firewall is active and enabled on system startup
?2004h0;root@vmi1146819: ~root@vmi1146819:~# ufw status numbered
Status: active

     To				Action	    From
     --				------	    ----
[ 1] 10250/tcp			ALLOW IN    Anywhere
[ 2] 30000:32767/tcp		ALLOW IN    Anywhere
[ 3] 22/tcp			ALLOW IN    Anywhere
[ 4] 10250/tcp (v6)		ALLOW IN    Anywhere (v6)
[ 5] 30000:32767/tcp (v6)	ALLOW IN    Anywhere (v6)
[ 6] 22/tcp (v6)		ALLOW IN    Anywhere (v6)

?2004h0;root@vmi1146819: ~root@vmi1146819:~# hostname
k8-14l
?2004h0;root@vmi1146819: ~root@vmi1146819:~# reboot
?2004h0;root@vmi1146819: ~root@vmi1146819:~# Connection to k8-1.v-site.net closed by remote host.
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:49:49]-$Bmssh root@k8-0.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:49:58 CET 2026

  System load:		 0.0
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 129
  Users logged in:	 1
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***
  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:42:28 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# ufw status numbered
Status: active

     To				Action	    From
     --				------	    ----
[ 1] 6443/tcp			ALLOW IN    Anywhere
[ 2] 2379:2380/tcp		ALLOW IN    Anywhere
[ 3] 10250/tcp			ALLOW IN    Anywhere
[ 4] 10257/tcp			ALLOW IN    Anywhere
[ 5] 10259/tcp			ALLOW IN    Anywhere
[ 6] 22/tcp			ALLOW IN    Anywhere
[ 7] 80/tcp			ALLOW IN    Anywhere
[ 8] 443/tcp			ALLOW IN    Anywhere
[ 9] 6443/tcp (v6)		ALLOW IN    Anywhere (v6)
[10] 2379:2380/tcp (v6)		ALLOW IN    Anywhere (v6)
[11] 10250/tcp (v6)		ALLOW IN    Anywhere (v6)
[12] 10257/tcp (v6)		ALLOW IN    Anywhere (v6)
[13] 10259/tcp (v6)		ALLOW IN    Anywhere (v6)
[14] 22/tcp (v6)		ALLOW IN    Anywhere (v6)
[15] 80/tcp (v6)		ALLOW IN    Anywhere (v6)
[16] 443/tcp (v6)		ALLOW IN    Anywhere (v6)

?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:50:21]-$Bmssh root@k8-1.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:50:29 CET 2026

  System load:		 0.11
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 133
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:42:45 2026 from 73.222.150.26
?2004h0;root@k8-1: ~root@k8-1:~# ufw sKtatus numbered
Status: active

     To				Action	    From
     --				------	    ----
[ 1] 10250/tcp			ALLOW IN    Anywhere
[ 2] 30000:32767/tcp		ALLOW IN    Anywhere
[ 3] 22/tcp			ALLOW IN    Anywhere
[ 4] 10250/tcp (v6)		ALLOW IN    Anywhere (v6)
[ 5] 30000:32767/tcp (v6)	ALLOW IN    Anywhere (v6)
[ 6] 22/tcp (v6)		ALLOW IN    Anywhere (v6)

?2004h0;root@k8-1: ~root@k8-1:~# exit
logout
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:50:47]-$Bmssh root@k8-1P2.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:51:07 CET 2026

  System load:		 0.0
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 126
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***
  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:42:09 2026 from 73.222.150.26
?2004h0;root@vmi1159519: ~root@vmi1159519:~# vi /etc/hosts
?1049h22;0;0t>4;2m?1h?2004h?1004h1;50r?12h?12l22;2t22;1t27m23m29mmH2J?25l50;1H"/etc/hosts" 15L, 565B2;1H▽6n2;1H	 3;1Hzz0%m6n3;1H	   1;1H>c10;?11;?1;1H34m# Your system has configured 'manage_etc_hosts' as True.
```bash
# As a result, if you wish for changes to this file to persistm2;63HK3;1H34m# then you will need to eitherm3;31HK4;1H34m# a.) make changes to the master file in /etc/cloud/templates/hosts.debian.tmpl
```
```bash
# b.) change or remove the value of 'manage_etc_hosts' in
```
```bash
#     /etc/cloud/cloud.cfg or cloud-config from user-data
```
```bash
#m
```
127.0.1.1 vmi1159519.contaboserver.net vmi1159519
127.0.0.1 localhost

34m# The following lines are desirable for IPv6 capable hostsm
::1 localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

94m~												  17;1H~											      18;1H~												  19;1H~											      20;1H~												  21;1H~											      22;1H~												  23;1H~											      24;1H~												  25;1H~											      26;1H~												  27;1H~											      28;1H~												  29;1H~											      30;1H~												  31;1H~											      32;1H~												  33;1H~											      34;1H~												  35;1H~											      36;1H~												  37;1H~											      38;1H~												  39;1H~											      40;1H~												  41;1H~											      42;1H~												  43;1H~											      44;1H~												  45;1H~											      46;1H~												  47;1H~											      48;1H~												  49;1H~											      m50;78H1,111CAll1;1H?25h?4m+q436f+q6b75+q6b64+q6b72+q6b6c+q2332+q2334+q2569+q2a37+q6b31$q q?12$p?25l50;68H:1;1H50;69H01;1H50;70H01;1H50;71H01;1H50;72H01;1H50;73H/1;1H50;74H01;1H50;75H01;1H50;76H01;1H50;77H01;1H50;68H		1;1H27m23m29mmH2J1;1H96m# Your system has configured 'manage_etc_hosts' as True.
```bash
# As a result, if you wish for changes to this file to persist
```
```bash
# then you will need to either
```
```bash
# a.) make changes to the master file in /etc/cloud/templates/hosts.debian.tmpl
```
```bash
# b.) change or remove the value of 'manage_etc_hosts' in
```
```bash
#     /etc/cloud/cloud.cfg or cloud-config from user-data
```
```bash
#m
```
127.0.1.1 vmi1159519.contaboserver.net vmi1159519
127.0.0.1 localhost

96m# The following lines are desirable for IPv6 capable hostsm
::1 localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

23;2t23;1t>4;m"/etc/hosts"?15L,2546B;written;1H50;68H	2;1H50;78H22;1H?25h?25l50;68H~@k2;1H50;68H17;3;1H50;78H33;1H?25h?25l50;68H~@k3;1H50;68H	  4;1H50;78H44;1H?25h?25l50;68H~@k4;1H50;68H   5;1H50;78H55;1H?25h?25l50;68H~@k5;1H50;68H   6;1H50;78H66;1H?25h?25l50;68H~@k6;1H50;68H	 7;1H50;78H77;1H?25h?25l50;68H~@k7;1H50;68H   8;1H50;78H88;1H?25h?25l50;68H~@k8;1H50;68H   8;2H50;80H28;2H?25h?25l50;68H~@k8;2H50;68H	8;3H50;80H38;3H?25h?25l50;68H~@k8;3H50;68H   8;4H50;80H48;4H?25h?25l50;68H~@k8;4H50;68H~  8;5H50;80H58;5H?25h?25l50;68H~@k8;5H50;68H   8;6H50;80H68;6H?25h?25l50;68H~@k8;6H50;68H   8;7H50;80H78;7H?25h?25l50;68H~@k8;7H50;68H	 8;8H50;80H88;8H?25h?25l50;68H~@k8;8H50;68H   8;9H50;80H98;9H?25h?25l50;68H~@k8;9H50;68H   8;10H50;80H108;10H?25h?25l50;68H~@k8;10H50;68H   8;11H50;81H18;11H?25h?25l50;68H~@k8;11H50;68H   8;12H50;81H28;12H?25h?25l50;68H~@k8;12H50;68H   8;11H50;81H18;11H?25h?25l50;68Hc8;11H?25h?25l50;69Hw8;11H50;68H  8;11H50;1H1m-- INSERT --m50;14HK50;78H8,1110CAll8;11H.contaboserver.net vmi11595198;40HK8;11H?25h?25lk.contaboserver.net vmi115951950;81H28;12H?25h?25l8.contaboserver.net vmi115951950;81H38;13H?25h?25l-.contaboserver.net vmi115951950;81H48;14H?25h?25l2.contaboserver.net vmi115951950;81H58;15H?25h50;1HK8;14H?25l50;68H^[8;14H50;68H  8;15H50;78H8,1410CAll8;14H?25h?25l50;68H~@k8;14H50;68H   8;15H50;81H58;15H?25h?25l50;68H~@k8;15H50;68H   8;16H50;81H68;16H?25h?25l50;68H~@k8;16H50;68H   8;17H50;81H78;17H?25h?25l50;68H~@k8;17H50;68H   8;18H50;81H88;18H?25h?25l50;68H~@k8;18H50;68H   8;19H50;81H98;19H?25h?25l50;68H~@k8;19H50;68H   8;20H50;80H208;20H?25h?25l50;68H~@k8;20H50;68H   8;21H50;81H18;21H?25h?25l50;68H~@k8;21H50;68H   8;22H50;81H28;22H?25h?25l50;68H~@k8;22H50;68H   8;23H50;81H38;23H?25h?25l50;68H~@k8;23H50;68H   8;24H50;81H48;24H?25h?25l50;68H~@k8;24H50;68H   8;25H50;81H58;25H?25h?25l50;68H~@k8;25H50;68H   8;26H50;81H68;26H?25h?25l50;68H~@k8;26H50;68H   8;27H50;81H78;27H?25h?25l50;68H~@k8;27H50;68H   8;28H50;81H88;28H?25h?25l50;68H~@k8;28H50;68H1H~8;29H50;81H98;29H?25h?25l50;68H~@k8;29H50;68H   8;30H50;80H308;30H?25h?25l50;68H~@k8;30H50;68H37;8;31H50;81H18;31H?25h?25l50;68H~@k8;31H50;68H   8;32H50;81H28;32H?25h?25l50;68H~@k8;32H50;68H   8;33H50;81H38;33H?25h?25l50;68H~@k8;33H50;68H   8;34H50;81H48;34H?25h?25l50;68H.8;34H50;68H 8;34H50;1H1m--~INSERT --m50;78HK50;78H8,3410CAll50;1HK8;34Hk8-28;38HK50;78H8,3710CAll8;37H?25h?25l50;68H~@k8;37H50;68H	  8;36H50;81H68;36H?25h?25l50;68H~@k8;36H50;68H	  8;35H50;81H58;35H?25h?25l50;68H~@k8;35H50;68H~  8;34H50;81H48;34H?25h?25l50;68H~@k8;34H50;68H	  8;33H50;81H38;33H?25h?25l50;68H~@k8;33H50;68H2;18;32H50;81H28;32H?25h?25l50;68H~@k8;32H50;68H	  8;31H50;81H18;31H?25h?25l50;81H08;30H?25h?25l50;68H~@k8;30H50;68H   8;29H50;80H298;29H?25h?25l50;68H~@k8;29H50;68H   8;28H50;81H88;28H?25h?25l50;68H~@k8;28H50;68H   8;27H50;81H78;27H?25h?25l50;68H~@k8;27H50;68H   8;26H50;81H68;26H?25h?25l50;68H~@k8;26H50;68H   8;25H50;81H58;25H?25h?25l50;68H~@k8;25H50;68H   8;24H50;81H48;24H?25h?25l50;68H~@k8;24H50;68H   8;23H50;81H38;23H?25h?25l50;68H~@k8;23H50;68H   8;22H50;81H28;22H?25h?25l50;68H~@k8;22H50;68H;1H8;21H50;81H18;21H?25h?25l50;68H~@k8;21H50;68H   8;20H50;81H08;20H?25h?25l50;68H~@k8;20H50;68H  48;19H50;80H198;19H?25h?25l50;68H~@k8;19H50;68H	8;18H50;81H88;18H?25h?25l50;68H~@k8;18H50;68H	8;17H50;81H78;17H?25h?25l50;68H~@k8;17H50;68H	8;16H50;81H68;16H?25h?25l50;68Hc8;16H?25h?25l50;69Hw8;16H50;68H118;16H50;1H1m-- INSERT --m50;78HK50;78H8,1610CAll8;16H.net k8-28;25HK8;16H?25h?25lv.net k8-250;81H78;17H?25h?25l-.net k8-250;81H88;18H?25h?25ls.net k8-250;81H98;19H?25h?25li.net k8-250;80H208;20H?25h?25lt.net k8-250;81H18;21H?25h?25le.net k8-250;81H28;22H?25h50;1HK8;21H?25l50;68H^[8;21H50;68H  8;22H50;78H8,2110CAll8;21H?25h?25l50;68H:8;21H50;68HK50;1H:?25hwq
?1004l?2004l?1l?1049l23;0;0t?25h>4;m?2004h0;root@vmi1159519: ~root@vmi1159519:~# ufw status
Status: inactive
?2004h0;root@vmi1159519: ~root@vmi1159519:~# 7msudo ufw allow 10250/tcp27m
7msudo ufw allow 30000:32sudotufw7allow 10250/tcp
sudo ufw allow 30000:32767/tcp
Ruleslupdated
Rules updated (v6)
Rules updated
Rules updated (v6)
?2004h0;root@vmi1159519: ~root@vmi1159519:~# sudo ufw allow 22/tcp
Ruleslupdated
Rules updated (v6)
?2004h0;root@vmi1159519: ~root@vmi1159519:~# ufw enable
Command may disrupt existing ssh connections. Proceed with operation (y|n)? y
Firewall is active and enabled on system startup
?2004h0;root@vmi1159519: ~root@vmi1159519:~# hostname
vmi1159519
?2004h0;root@vmi1159519: ~root@vmi1159519:~# vi /etc/hosts
?1049h22;0;0t>4;2m?1h?2004h?1004h1;50r?12h?12l22;2t22;1t27m23m29mmH2J?25l50;1H"/etc/hosts" 15L, 546B2;1H▽6n2;1H	 3;1Hzz0%m6n3;1H	   1;1H>c10;?11;?1;1H34m# Your system has configured 'manage_etc_hosts' as True.
```bash
# As a result, if you wish for changes to this file to persistm2;63HK3;1H34m# then you will need to eitherm3;31HK4;1H34m# a.) make changes to the master file in /etc/cloud/templates/hosts.debian.tmpl
```
```bash
# b.) change or remove the value of 'manage_etc_hosts' in
```
```bash
#     /etc/cloud/cloud.cfg or cloud-config from user-data
```
```bash
#m
```
127.0.1.1 k8-2.v-site.net k8-2
127.0.0.1 localhost

34m# The following lines are desirable for IPv6 capable hostsm
::1 localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

94m~												  17;1H~											      18;1H~												  19;1H~											      20;1H~												  21;1H~											      22;1H~												  23;1H~											      24;1H~												  25;1H~											      26;1H~												  27;1H~											      28;1H~												  29;1H~											      30;1H~												  31;1H~											      32;1H~												  33;1H~											      34;1H~												  35;1H~											      36;1H~												  37;1H~											      38;1H~												  39;1H~											      40;1H~												  41;1H~											      42;1H~												  43;1H~											      44;1H~												  45;1H~											      46;1H~												  47;1H~											      48;1H~												  49;1H~											      m50;78H8,2110CAll8;21H?25h?4m+q436f+q6b75+q6b64+q6b72+q6b6c+q2332+q2334+q2569+q2a37+q6b31$q q?12$p?25l50;68H:8;21H50;69H08;21H50;70H08;21H50;71H08;21H50;72H08;21H50;73H/8;21H50;74H08;21H50;75H08;21H50;76H08;21H50;77H08;21H50;68H	    8;21H27m23m29mmH2J1;1H96m# Your system has configured 'manage_etc_hosts' as True.
```bash
# As a result, if you wish for changes to this file to persist
```
```bash
# then you will need to either
```
```bash
# a.) make changes to the master file in /etc/cloud/templates/hosts.debian.tmpl
```
```bash
# b.) change or remove the value of 'manage_etc_hosts' in
```
```bash
#     /etc/cloud/cloud.cfg or cloud-config from user-data
```
```bash
#m
```
127.0.1.1 k8-2.v-site.net k8-2
127.0.0.1 localhost

96m# The following lines are desirable for IPv6 capable hostsm
::1 localhost ip6-localhost ip6-loopback
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters

?25l?2004l>4;m23;2t23;1t50;1HK50;1H?1004l?2004l?1l?1049l23;0;0t?25h>4;m?2004h0;root@vmi1159519:5~root@vmi1159519:~#;hostnamectl set-hostname k8-2						      18;1H~												  19;1H~											      20;1H~												  21;1H~											      22;1H~												  23;1H~											      24;1H~												  25;1H~											      26;1H~												  27;1H~											      28;1H~												  29;1H~											      30;1H~												  31;1H~											      32;1H~												  33;1H~											      34;1H~												  35;1H~											      36;1H~												  37;1H~											      38;1H~												  39;1H~											      40;1H~												  41;1H~											      42;1H~												  43;1H~											      44;1H~												  45;1H~											      46;1H~												  47;1H~											      48;1H~												  49;1H~											      m50;78H8,2110CAll
?2004h0;root@vmi1159519: ~root@vmi1159519:~# hostname
k8-24l
?2004h0;root@vmi1159519: ~root@vmi1159519:~# exit
logout
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:55:08]-$Bmssh root@k8-2.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:55:14 CET 2026

  System load:		 0.0
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 130
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***
  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:51:08 2026 from 73.222.150.26
?2004h0;root@k8-2: ~root@k8-2:~# reboot
?2004h0;root@k8-2: ~root@k8-2:~# Connection to k8-2.v-site.net closed by remote host.
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:55:21]-$Bmssh root@k8-1P1.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:55:31 CET 2026

  System load:		 0.0
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 133
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:50:30 2026 from 73.222.150.26
?2004h0;root@k8-1: ~root@k8-1:~# exit
logout
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:55:54]-$Bmssh root@k8-1P0.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-90-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:56:04 CET 2026

  System load:		 0.0
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 128
  Users logged in:	 1
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


*** System restart required ***
  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:49:59 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# reboot
?2004h0;root@k8-0: ~root@k8-0:~# Connection to k8-0.v-site.net closed by remote host.
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:56:10]-$Bmssh root@k8-1P2.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 09:56:19 CET 2026

  System load:		 0.91
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 129
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:55:14 2026 from 73.222.150.26
?2004h0;root@k8-2: ~root@k8-2:~# exit
logout
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 00:56:30]-$Bm# rCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
?2004hl0r3zz@tarnover:[2026-02-12 00:57:10]-$Bm# all node KhaveK ssh key login
l0r3zz@tarnover:[2026-02-12C00:57:56]-$BmCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCct2Pion-environment/~A~AAAAent/~
CCCCCCCCCCCCCCCCCK
l0r3zz@tarnover:[2026-02-12-08:15:54]-$BmCCCCCCCCCCCCCCCCCCCCCCCChttps://kubernetes.io/docs/setup/production-environment/tools/kubeadm/ent/tools/kubeadm/27mA
l0r3zz@tarnover:[2026-02-12-08:20:03]-$BmCCCCCCCCCCCCCCCCCCCCCCChttps://kubernetes.io/docs/reference/networking/ports-and-protocols/rts-and-protocols/27mA
ACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCK!/TCP !!
?2004hl0r3zz@tarnover:[2026-02-12 08:22:55]-$Bmssh root@k8-0.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 17:23:54 CET 2026

  System load:		 0.08
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 125
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:56:04 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip

To			   Action      From
--			   ------      ----
6443/tcp		   ALLOW IN    Anywhere
2379:2380/tcp		   ALLOW IN    Anywhere
10250/tcp		   ALLOW IN    Anywhere
10257/tcp		   ALLOW IN    Anywhere
10259/tcp		   ALLOW IN    Anywhere
22/tcp			   ALLOW IN    Anywhere
80/tcp			   ALLOW IN    Anywhere
443/tcp			   ALLOW IN    Anywhere
6443/tcp (v6)		   ALLOW IN    Anywhere (v6)
2379:2380/tcp (v6)	   ALLOW IN    Anywhere (v6)
10250/tcp (v6)		   ALLOW IN    Anywhere (v6)
10257/tcp (v6)		   ALLOW IN    Anywhere (v6)
10259/tcp (v6)		   ALLOW IN    Anywhere (v6)
22/tcp (v6)		   ALLOW IN    Anywhere (v6)
80/tcp (v6)		   ALLOW IN    Anywhere (v6)
443/tcp (v6)		   ALLOW IN    Anywhere (v6)

?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 08:25:06]-$Bmssh root@k8-1P1.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 17:25:16 CET 2026

  System load:		 0.15
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 126
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:55:31 2026 from 73.222.150.26
?2004h0;root@k8-1: ~root@k8-1:~# ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip

To			   Action      From
--			   ------      ----
10250/tcp		   ALLOW IN    Anywhere
30000:32767/tcp		   ALLOW IN    Anywhere
22/tcp			   ALLOW IN    Anywhere
10250/tcp (v6)		   ALLOW IN    Anywhere (v6)
30000:32767/tcp (v6)	   ALLOW IN    Anywhere (v6)
22/tcp (v6)		   ALLOW IN    Anywhere (v6)

?2004h0;root@k8-1: ~root@k8-1:~# ufw allow 10256/tcp
Rule4added
Rule added (v6)
?2004h0;root@k8-1: ~root@k8-1:~# ## added for kube-proxy
CCCCCCCCCCCCC4Pufw 1Pstatus2verbose added for kube-proxy
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip

To			   Action      From
--			   ------      ----
10250/tcp		   ALLOW IN    Anywhere
30000:32767/tcp		   ALLOW IN    Anywhere
22/tcp			   ALLOW IN    Anywhere
10256/tcp		   ALLOW IN    Anywhere
10250/tcp (v6)		   ALLOW IN    Anywhere (v6)
30000:32767/tcp (v6)	   ALLOW IN    Anywhere (v6)
22/tcp (v6)		   ALLOW IN    Anywhere (v6)
10256/tcp (v6)		   ALLOW IN    Anywhere (v6)

?2004h0;root@k8-1: ~root@k8-1:~# exit
logout
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 08:27:57]-$Bmssh root@k8-1P2.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 17:28:06 CET 2026

  System load:		 0.0
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 127
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 09:56:20 2026 from 73.222.150.26
?2004h0;root@k8-2: ~root@k8-2:~# ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip

To			   Action      From
--			   ------      ----
10250/tcp		   ALLOW IN    Anywhere
30000:32767/tcp		   ALLOW IN    Anywhere
22/tcp			   ALLOW IN    Anywhere
10250/tcp (v6)		   ALLOW IN    Anywhere (v6)
30000:32767/tcp (v6)	   ALLOW IN    Anywhere (v6)
22/tcp (v6)		   ALLOW IN    Anywhere (v6)

?2004h0;root@k8-2: ~root@k8-2:~# ufw allow 10256/tcp
Rule4added
Rule added (v6)
?2004h0;root@k8-2: ~root@k8-2:~# ufw 1Pstatus2verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), disabled (routed)
New profiles: skip

To			   Action      From
--			   ------      ----
10250/tcp		   ALLOW IN    Anywhere
30000:32767/tcp		   ALLOW IN    Anywhere
22/tcp			   ALLOW IN    Anywhere
10256/tcp		   ALLOW IN    Anywhere
10250/tcp (v6)		   ALLOW IN    Anywhere (v6)
30000:32767/tcp (v6)	   ALLOW IN    Anywhere (v6)
22/tcp (v6)		   ALLOW IN    Anywhere (v6)
10256/tcp (v6)		   ALLOW IN    Anywhere (v6)

?2004h0;root@k8-2: ~root@k8-2:~# exit
logout
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 08:29:05]-$Bmssh root@k8-0.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 17:35:51 CET 2026

  System load:		 0.02
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 125
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 17:23:56 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# swapon -s
?2004h0;root@k8-0: ~root@k8-0:~# top
?1h?25lH2JBmtop - 17:36:24 up  7:40,  1 user,  load average: 0.01, 0.01, 0.00Bm39;49mBm39;49mK
Tasks:Bm39;49m1m 122 Bm39;49mtotal,Bm39;49m1m	2 Bm39;49mrunning,Bm39;49m1m 120 Bm39;49msleeping,Bm39;49m1m   0 Bm39;49mstopped,Bm39;49m1m   0 Bm39;49mzombieBm39;49mBm39;49mK
%Cpu(s):Bm39;49m1m  0.0 Bm39;49mus,Bm39;49m1m  2.3 Bm39;49msy,Bm39;49m1m  0.0 Bm39;49mni,Bm39;49m1m 97.7 Bm39;49mid,Bm39;49m1m	0.0 Bm39;49mwa,Bm39;49m1m  0.0 Bm39;49mhi,Bm39;49m1m  0.0 Bm39;49msi,Bm39;49m1m	 0.0 Bm39;49mstBm39;49mBm Bm39;49mBm39;49mK
MiB Mem :Bm39;49m1m   7941.2 Bm39;49mtotal,Bm39;49m1m	7543.8 Bm39;49mfree,Bm39;49m1m	  445.3 Bm39;49mused,Bm39;49m1m	   180.5 Bm39;49mbuff/cacheBm39;49mBm Bm39;49mBm    Bm39;49mBm39;49mK
MiB Swap:Bm39;49m1m	 0.0 Bm39;49mtotal,Bm39;49m1m	   0.0 Bm39;49mfree,Bm39;49m1m	    0.0 Bm39;49mused.Bm39;49m1m	  7495.9 Bm39;49mavail Mem Bm39;49mBm39;49mK
K
7m    PID USER	    PR	NI    VIRT    RES    SHR S  %CPU  %MEM	   TIME+ COMMAND		 Bm39;49mK
Bm	1 root	    20	 0   22116  13320   9568 S   0.0   0.2	 0:11.12 systemd		 Bm39;49mK
Bm	2 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.07 kthreadd		 Bm39;49mK
Bm	3 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 pool_workqueue_release	 Bm39;49mK
Bm	4 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-rcu_g	 Bm39;49mK
Bm	5 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-rcu_p	 Bm39;49mK
Bm	6 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-slub_	 Bm39;49mK
Bm	7 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-netns	 Bm39;49mK
Bm     10 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/0:0H-kblockd	 Bm39;49mK
Bm     12 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-mm_pe	 Bm39;49mK
Bm     13 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_kthread	 Bm39;49mK
Bm     14 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_rude_kthread	 Bm39;49mK
Bm     15 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_trace_kthread Bm39;49mK
Bm     16 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.24 ksoftirqd/0		 Bm39;49mK
Bm     17 root	    20	 0	 0	0      0 I   0.0   0.0	 0:26.67 rcu_preempt		 Bm39;49mK
Bm     18 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.23 migration/0		 Bm39;49mK
Bm     19 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/0		 Bm39;49mK
Bm     20 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/0		 Bm39;49mK
Bm     21 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/1		 Bm39;49mK
Bm     22 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/1		 Bm39;49mK
Bm     23 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.60 migration/1		 Bm39;49mK
Bm     24 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.75 ksoftirqd/1		 Bm39;49mK
Bm     26 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/1:0H-events_hi+ Bm39;49mK
Bm     27 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/2		 Bm39;49mK
Bm     28 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/2		 Bm39;49mK
Bm     29 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.61 migration/2		 Bm39;49mK
Bm     30 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.37 ksoftirqd/2		 Bm39;49mK
Bm     32 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/2:0H-events_hi+ Bm39;49mK
Bm     33 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/3		 Bm39;49mK
Bm     34 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/3		 Bm39;49mK
Bm     35 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.60 migration/3		 Bm39;49mK
Bm     36 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.20 ksoftirqd/3		 Bm39;49mK
Bm     38 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/3:0H-events_hi+ Bm39;49mK
Bm     39 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 kdevtmpfs		 Bm39;49mK
Bm     40 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-inet_	 Bm39;49mK
Bm     41 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 kauditd		 Bm39;49mK
Bm     42 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.02 khungtaskd		 Bm39;49mK
Bm     43 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 oom_reaper		 Bm39;49mK
Bm     46 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-write	 Bm39;49mK
Bm     47 root	    20	 0	 0	0      0 S   0.0   0.0	 0:02.11 kcompactd0		 Bm39;49mK
Bm     48 root	    25	 5	 0	0      0 S   0.0   0.0	 0:00.00 ksmd			 Bm39;49mK
Bm     49 root	    39	19	 0	0      0 S   0.0   0.0	 0:00.00 khugepaged		 Bm39;49mK
Bm     50 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-kinte	 Bm39;49mK
Bm     51 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-kbloc	 Bm39;49mKHBmtop - 17:36:27 up	7:40,  1 user,	load average: 0.01, 0.01, 0.00Bm39;49mBm39;49mK
Tasks:Bm39;49m1m 121 Bm39;49mtotal,Bm39;49m1m	1 Bm39;49mrunning,Bm39;49m1m 120 Bm39;49msleeping,Bm39;49m1m   0 Bm39;49mstopped,Bm39;49m1m   0 Bm39;49mzombieBm39;49mBm39;49mK
%Cpu(s):Bm39;49m1m  0.1 Bm39;49mus,Bm39;49m1m  0.2 Bm39;49msy,Bm39;49m1m  0.0 Bm39;49mni,Bm39;49m1m 99.8 Bm39;49mid,Bm39;49m1m	0.0 Bm39;49mwa,Bm39;49m1m  0.0 Bm39;49mhi,Bm39;49m1m  0.0 Bm39;49msi,Bm39;49m1m	 0.0 Bm39;49mstBm39;49mBm Bm39;49mBm39;49mK
MiB Mem :Bm39;49m1m   7941.2 Bm39;49mtotal,Bm39;49m1m	7547.3 Bm39;49mfree,Bm39;49m1m	  441.6 Bm39;49mused,Bm39;49m1m	   180.6 Bm39;49mbuff/cacheBm39;49mBm Bm39;49mBm    Bm39;49mBm39;49mK
MiB Swap:Bm39;49m1m	 0.0 Bm39;49mtotal,Bm39;49m1m	   0.0 Bm39;49mfree,Bm39;49m1m	    0.0 Bm39;49mused.Bm39;49m1m	  7499.6 Bm39;49mavail Mem Bm39;49mBm39;49mK
K

Bm   1957 root	    20	 0	 0	0      0 I   0.3   0.0	 0:02.85 kworker/2:0-events_fre+ Bm39;49mK
Bm   7841 root	    20	 0	 0	0      0 I   0.3   0.0	 0:00.71 kworker/u8:2-events_fr+ Bm39;49mK
Bm	1 root	    20	 0   22116  13320   9568 S   0.0   0.2	 0:11.12 systemd		 Bm39;49mK
Bm	2 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.07 kthreadd		 Bm39;49mK
Bm	3 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 pool_workqueue_release	 Bm39;49mK
Bm	4 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-rcu_g	 Bm39;49mK
Bm	5 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-rcu_p	 Bm39;49mK
Bm	6 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-slub_	 Bm39;49mK
Bm	7 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-netns	 Bm39;49mK
Bm     10 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/0:0H-kblockd	 Bm39;49mK
Bm     12 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-mm_pe	 Bm39;49mK
Bm     13 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_kthread	 Bm39;49mK
Bm     14 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_rude_kthread	 Bm39;49mK
Bm     15 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_trace_kthread Bm39;49mK
Bm     16 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.24 ksoftirqd/0		 Bm39;49mK
Bm     17 root	    20	 0	 0	0      0 I   0.0   0.0	 0:26.67 rcu_preempt		 Bm39;49mK
Bm     18 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.23 migration/0		 Bm39;49mK
Bm     19 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/0		 Bm39;49mK
Bm     20 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/0		 Bm39;49mK
Bm     21 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/1		 Bm39;49mK
Bm     22 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/1		 Bm39;49mK
Bm     23 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.60 migration/1		 Bm39;49mK
Bm     24 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.75 ksoftirqd/1		 Bm39;49mK
Bm     26 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/1:0H-events_hi+ Bm39;49mK
Bm     27 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/2		 Bm39;49mK
Bm     28 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/2		 Bm39;49mK
Bm     29 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.61 migration/2		 Bm39;49mK
Bm     30 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.37 ksoftirqd/2		 Bm39;49mK
Bm     32 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/2:0H-events_hi+ Bm39;49mK
Bm     33 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/3		 Bm39;49mK
Bm     34 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/3		 Bm39;49mK
Bm     35 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.60 migration/3		 Bm39;49mK
Bm     36 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.20 ksoftirqd/3		 Bm39;49mK
Bm     38 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/3:0H-events_hi+ Bm39;49mK
Bm     39 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 kdevtmpfs		 Bm39;49mK
Bm     40 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-inet_	 Bm39;49mK
Bm     41 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 kauditd		 Bm39;49mK
Bm     42 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.02 khungtaskd		 Bm39;49mK
Bm     43 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 oom_reaper		 Bm39;49mK
Bm     46 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-write	 Bm39;49mK
Bm     47 root	    20	 0	 0	0      0 S   0.0   0.0	 0:02.11 kcompactd0		 Bm39;49mK
Bm     48 root	    25	 5	 0	0      0 S   0.0   0.0	 0:00.00 ksmd			 Bm39;49mK
Bm     49 root	    39	19	 0	0      0 S   0.0   0.0	 0:00.00 khugepaged		 Bm39;49mKHBmtop - 17:36:30 up	7:40,  1 user,	load average: 0.01, 0.01, 0.00Bm39;49mBm39;49mK
Tasks:Bm39;49m1m 122 Bm39;49mtotal,Bm39;49m1m	1 Bm39;49mrunning,Bm39;49m1m 121 Bm39;49msleeping,Bm39;49m1m   0 Bm39;49mstopped,Bm39;49m1m   0 Bm39;49mzombieBm39;49mBm39;49mK
%Cpu(s):Bm39;49m1m  0.1 Bm39;49mus,Bm39;49m1m  0.2 Bm39;49msy,Bm39;49m1m  0.0 Bm39;49mni,Bm39;49m1m 99.5 Bm39;49mid,Bm39;49m1m	0.2 Bm39;49mwa,Bm39;49m1m  0.0 Bm39;49mhi,Bm39;49m1m  0.0 Bm39;49msi,Bm39;49m1m	 0.0 Bm39;49mstBm39;49mBm Bm39;49mBm39;49mK


K

Bm1m   9268 root      20   0   12348   6108   3872 R   0.3   0.1   0:00.02 top			   Bm39;49mK
Bm   9269 root	    20	 0   12152   8380   7256 S   0.3   0.1	 0:00.01 sshd			 Bm39;49mK
Bm   9270 sshd	    20	 0   12152   6036   4908 S   0.3   0.1	 0:00.01 sshd			 Bm39;49mK
Bm	1 root	    20	 0   22116  13320   9568 S   0.0   0.2	 0:11.12 systemd		 Bm39;49mK
Bm	2 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.07 kthreadd		 Bm39;49mK
Bm	3 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 pool_workqueue_release	 Bm39;49mK
Bm	4 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-rcu_g	 Bm39;49mK
Bm	5 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-rcu_p	 Bm39;49mK
Bm	6 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-slub_	 Bm39;49mK
Bm	7 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-netns	 Bm39;49mK
Bm     10 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/0:0H-kblockd	 Bm39;49mK
Bm     12 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-mm_pe	 Bm39;49mK
Bm     13 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_kthread	 Bm39;49mK
Bm     14 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_rude_kthread	 Bm39;49mK
Bm     15 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_trace_kthread Bm39;49mK
Bm     16 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.24 ksoftirqd/0		 Bm39;49mK
Bm     17 root	    20	 0	 0	0      0 I   0.0   0.0	 0:26.67 rcu_preempt		 Bm39;49mK
Bm     18 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.23 migration/0		 Bm39;49mK
Bm     19 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/0		 Bm39;49mK
Bm     20 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/0		 Bm39;49mK
Bm     21 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/1		 Bm39;49mK
Bm     22 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/1		 Bm39;49mK
Bm     23 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.60 migration/1		 Bm39;49mK
Bm     24 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.75 ksoftirqd/1		 Bm39;49mK
Bm     26 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/1:0H-events_hi+ Bm39;49mK
Bm     27 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/2		 Bm39;49mK
Bm     28 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/2		 Bm39;49mK
Bm     29 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.61 migration/2		 Bm39;49mK
Bm     30 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.37 ksoftirqd/2		 Bm39;49mK
Bm     32 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/2:0H-events_hi+ Bm39;49mK
Bm     33 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/3		 Bm39;49mK
Bm     34 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/3		 Bm39;49mK
Bm     35 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.60 migration/3		 Bm39;49mK
Bm     36 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.20 ksoftirqd/3		 Bm39;49mK
Bm     38 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/3:0H-events_hi+ Bm39;49mK
Bm     39 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 kdevtmpfs		 Bm39;49mK
Bm     40 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-inet_	 Bm39;49mK
Bm     41 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 kauditd		 Bm39;49mK
Bm     42 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.02 khungtaskd		 Bm39;49mK
Bm     43 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 oom_reaper		 Bm39;49mK
Bm     46 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-write	 Bm39;49mK
Bm     47 root	    20	 0	 0	0      0 S   0.0   0.0	 0:02.11 kcompactd0		 Bm39;49mK
Bm     48 root	    25	 5	 0	0      0 S   0.0   0.0	 0:00.00 ksmd			 Bm39;49mKHBmtop - 17:36:33 up	7:40,  1 user,	load average: 0.01, 0.01, 0.00Bm39;49mBm39;49mK

%Cpu(s):Bm39;49m1m  0.3 Bm39;49mus,Bm39;49m1m  0.5 Bm39;49msy,Bm39;49m1m  0.0 Bm39;49mni,Bm39;49m1m 99.2 Bm39;49mid,Bm39;49m1m	0.0 Bm39;49mwa,Bm39;49m1m  0.0 Bm39;49mhi,Bm39;49m1m  0.0 Bm39;49msi,Bm39;49m1m	 0.0 Bm39;49mstBm39;49mBm Bm39;49mBm39;49mK
MiB Mem :Bm39;49m1m   7941.2 Bm39;49mtotal,Bm39;49m1m	7541.0 Bm39;49mfree,Bm39;49m1m	  447.9 Bm39;49mused,Bm39;49m1m	   180.6 Bm39;49mbuff/cacheBm39;49mBm Bm39;49mBm    Bm39;49mBm39;49mK
MiB Swap:Bm39;49m1m	 0.0 Bm39;49mtotal,Bm39;49m1m	   0.0 Bm39;49mfree,Bm39;49m1m	    0.0 Bm39;49mused.Bm39;49m1m	  7493.3 Bm39;49mavail Mem Bm39;49mBm39;49mK
K

Bm   9269 root	    20	 0   14088   9596   8180 S   2.0   0.1	 0:00.07 sshd			 Bm39;49mK
Bm     17 root	    20	 0	 0	0      0 I   0.3   0.0	 0:26.68 rcu_preempt		 Bm39;49mK
Bm    326 root	    19	-1   50372  30168  29016 S   0.3   0.4	 0:16.61 systemd-journal	 Bm39;49mK
Bm   7841 root	    20	 0	 0	0      0 I   0.3   0.0	 0:00.72 kworker/u8:2-events_po+ Bm39;49mK
Bm   8713 root	    20	 0	 0	0      0 I   0.3   0.0	 0:00.23 kworker/u8:3-events_fr+ Bm39;49mK
Bm   9171 root	    20	 0   15244  10928   8788 S   0.3   0.1	 0:00.04 sshd			 Bm39;49mK
Bm   9270 sshd	    20	 0   12152   6100   4972 S   0.3   0.1	 0:00.02 sshd			 Bm39;49mK
Bm	1 root	    20	 0   22116  13320   9568 S   0.0   0.2	 0:11.12 systemd		 Bm39;49mK
Bm	2 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.07 kthreadd		 Bm39;49mK
Bm	3 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 pool_workqueue_release	 Bm39;49mK
Bm	4 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-rcu_g	 Bm39;49mK
Bm	5 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-rcu_p	 Bm39;49mK
Bm	6 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-slub_	 Bm39;49mK
Bm	7 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-netns	 Bm39;49mK
Bm     10 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/0:0H-kblockd	 Bm39;49mK
Bm     12 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-mm_pe	 Bm39;49mK
Bm     13 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_kthread	 Bm39;49mK
Bm     14 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_rude_kthread	 Bm39;49mK
Bm     15 root	    20	 0	 0	0      0 I   0.0   0.0	 0:00.00 rcu_tasks_trace_kthread Bm39;49mK
Bm     16 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.24 ksoftirqd/0		 Bm39;49mK
Bm     18 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.23 migration/0		 Bm39;49mK
Bm     19 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/0		 Bm39;49mK
Bm     20 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/0		 Bm39;49mK
Bm     21 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/1		 Bm39;49mK
Bm     22 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/1		 Bm39;49mK
Bm     23 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.60 migration/1		 Bm39;49mK
Bm     24 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.75 ksoftirqd/1		 Bm39;49mK
Bm     26 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/1:0H-events_hi+ Bm39;49mK
Bm     27 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/2		 Bm39;49mK
Bm     28 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/2		 Bm39;49mK
Bm     29 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.61 migration/2		 Bm39;49mK
Bm     30 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.37 ksoftirqd/2		 Bm39;49mK
Bm     32 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/2:0H-events_hi+ Bm39;49mK
Bm     33 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 cpuhp/3		 Bm39;49mK
Bm     34 root	   -51	 0	 0	0      0 S   0.0   0.0	 0:00.00 idle_inject/3		 Bm39;49mK
Bm     35 root	    rt	 0	 0	0      0 S   0.0   0.0	 0:00.60 migration/3		 Bm39;49mK
Bm     36 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.20 ksoftirqd/3		 Bm39;49mK
Bm     38 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/3:0H-events_hi+ Bm39;49mK
Bm     39 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 kdevtmpfs		 Bm39;49mK
Bm     40 root	     0 -20	 0	0      0 I   0.0   0.0	 0:00.00 kworker/R-inet_	 Bm39;49mK
Bm     41 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 kauditd		 Bm39;49mK
Bm     42 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.02 khungtaskd		 Bm39;49mK
Bm     43 root	    20	 0	 0	0      0 S   0.0   0.0	 0:00.00 oom_reaper		 Bm39;49mK?1l51;1H
?12l?25hK?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 08:37:28]-$Bm## these nodes have swap enabled so have to set
?2004hl0r3zz@tarnover:[2026-02-12 08:38:21]-$Bm### 7mfaifailSwapOn:lfalse
?2004hl0r3zz@tarnover:[2026-02-12 08:38:35]-$Bm### 7mmemorySwap:27m
l0r3zz@tarnover:[2026-02-12d08:38:35]-$BmCCCCmemorySwap:
ACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC#11PCCCCC
1@#1@#1@#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC24PsshBroot@k8-0.v-site.netavesswapeenabled so have to set
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 17:42:12 CET 2026

  System load:		 0.0
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 126
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 17:35:52 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# # Install kubeadm, kubelet, kubectl
?2004h0;root@k8-0: ~root@k8-0:~# apt update
Hit:1ohttp://archive.ubuntu.com/ubuntu noble InRelease
Get:2ahttp://archive.ubuntu.com/ubuntu noble-updates InRelease [126 kB]
Get:3ahttp://archive.ubuntu.com/ubuntu3noble-backports InRelease [126 kB]
Get:4ohttp://archive.ubuntu.com/ubuntu3noble-updates/main amd64 Packages [1,742 kB]
Get:5ahttp://archive.ubuntu.com/ubuntu3noble-updates/main Translation-en [325 kB]
Get:6 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Components [175 kB]
Get:7 http://archive.ubuntu.com/ubuntusnoble-updates/universe5amd643Components [386 kB]
Get:8 http://archive.ubuntu.com/ubuntusnoble-updates/restricted%amd64 Packages [2,594 kB]
Get:9 http://archive.ubuntu.com/ubuntu1noble-updates/restricted Translation-en [595 kB]
Get:10Phttp://archive.ubuntu.com/ubuntuhnoble-updates/restrictedmamd64 Components [212 B]
Get:11 http://archive.ubuntu.com/ubuntu noble-updates/multiverse amd64 Components [940 B]
Get:12Phttp://archive.ubuntu.com/ubuntuhnoble-backports/main amd64 Components [7,316 B]
Get:13 http://archive.ubuntu.com/ubuntu noble-backports/universe amd64 Components [10.5 kB]
Get:14 http://archive.ubuntu.com/ubuntu noble-backports/restricted amd64 Components [216 B]
Get:15Phttp://archive.ubuntu.com/ubuntusnoble-backports/multiverse amd64 Components [212 B]
Get:16ihttp://security.ubuntu.com/ubuntu noble-security InRelease [126 kB]	   961 kB/s 0s0m33m
Get:17ohttp://security.ubuntu.com/ubuntu noble-security/main amd64 Components [21.59kB]kB/s 0s0m33m
Get:18ahttp://security.ubuntu.com/ubuntutnoble-security/universe amd64 Components [74.2kkB] 0s0m33m
Get:198http://security.ubuntu.com/ubuntu noble-security/restricted amd64 Components9[212BB] 0s0m
Get:209http://security.ubuntu.com/ubuntu%noble-security/multiverse amd64 Components9[212BB] 0s0m
Fetchedo6,312]kBtina10s4(617rkB/s)]						   961 kB/s 0s0m33m
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
All packages are up to date.
CCCCCCCCCCCCCsudo:apt-getkinstall7-yuapt-transport-https-ca-certificates-curlsgpg-certificates curl gpg27m
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
ca-certificates is already the newest version (20240203).
ca-certificates set to manually installed.
curl is already the newest version (8.5.0-2ubuntu10.6).
curl set to manually installed.
gpg is already the newest version (2.4.4-2ubuntu17.4).
gpg set to manually installed.
The following NEW packages will be installed:
  apt-transport-https
0 upgraded, 1 newly installed, 0 to remove and 0 not upgraded.
Need to get 3,970 B of archives.
After this operation, 36.9 kB of additional disk space will be used.
Get:1ohttp://archive.ubuntu.com/ubuntu noble-updates/universe amd64 apt-transport-https all 2.8.3 [3,970 B]
Fetchedo3,970]B in 0s (18.7 kB/s)
Selecting previously unselected package apt-transport-https.
(Reading database ... 106428 files and directories currently installed.)
Preparing to unpack .../apt-transport-https_2.8.3_all.deb ...
Unpacking apt-transport-https (2.8.3) ...
Setting up apt-transport-https (2.8.3) ...
Scanning processes... [=======================================================================]
Scanning linux images... [====================================================================]

Running kernel seems to be up-to-date.

No services need to be restarted.

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
CCCCCCCCCCCCCcurl:-fsSLthttps://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key/|1sudodgpgR--dearmory-o /etc/apt/keyrings/kubernetes-apt-keyring.gpgrings/kubernetes-apt-keyring.gpg27mA
?2004h0;root@k8-0: ~root@k8-0:~# 7m# This overwrites any existing configuration in /etc/apt/sources.list.d/kubernetes27m7m.27m7mlist27m
CCCCCCCCCCCCC#iThis-overwritestanyyexistingbconfigurationeini/etc/apt/sources.list.d/kubernetes.list7ma27m7mble:/v1.35/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list27mAAA
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb0[signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /
?2004h0;root@k8-0: ~root@k8-0:~# 7msudo apt-get update27m
7msudo apt-get install -y kubelet kubeadm kubectl27m
CCCCCCCCCCCCCsudooapt-getlupdateeadm kubectl27mAA
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
Hit:1ohttp://archive.ubuntu.com/ubuntu noble InRelease
Hit:2ahttp://archive.ubuntu.com/ubuntu noble-updates InRelease
Hit:3ahttp://archive.ubuntu.com/ubuntu noble-backports InRelease
Get:4ohttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  InRelease [1,227 B]
Hit:5ahttp://security.ubuntu.com/ubuntu noble-security InRelease
Get:6ohttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  Packages [3,941 B]
Fetchedo5,168]Bsinr7s0(7604B/s)100%]
Reading package lists... Done
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following additional packages will be installed:
  cri-tools kubernetes-cni
The following NEW packages will be installed:
  cri-tools kubeadm kubectl kubelet kubernetes-cni
0 upgraded, 5 newly installed, 0 to remove and 0 not upgraded.
Need to get 92.0 MB of archives.
After this operation, 328 MB of additional disk space will be used.
Get:1ahttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/debfocri-tools 1.35.0-1.1 [16.2 MB]
Get:2Whttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubeadm 1.35.1-1.1 [12.4 MB]
Get:32https://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubectl 1.35.1-1.1 [11.5 MB]
Get:4Whttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubernetes-cni 1.8.0-1.1 [38.9 MB]
Get:54https://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubelet 1.35.1-1.1 [12.9 MB]
Fetchedo92.0gMB1in44sB(22.8MMB/s)%]
Selecting previously unselected package cri-tools.
(Reading database ... 106432 files and directories currently installed.)
Preparing to unpack .../cri-tools_1.35.0-1.1_amd64.deb ...
Unpacking cri-tools (1.35.0-1.1) ...
Selecting previously unselected package kubeadm.
Preparing to unpack .../kubeadm_1.35.1-1.1_amd64.deb ...
Unpacking kubeadm (1.35.1-1.1) ...
Selecting previously unselected package kubectl.
Preparing to unpack .../kubectl_1.35.1-1.1_amd64.deb ...
Unpacking kubectl (1.35.1-1.1) ...
Selecting previously unselected package kubernetes-cni.
Preparing to unpack .../kubernetes-cni_1.8.0-1.1_amd64.deb ...
Unpacking kubernetes-cni (1.8.0-1.1) ...
Selecting previously unselected package kubelet.
Preparing to unpack .../kubelet_1.35.1-1.1_amd64.deb ...
Unpacking kubelet (1.35.1-1.1) ...
Setting up kubectl (1.35.1-1.1) ...
Setting up cri-tools (1.35.0-1.1) ...
Setting up kubernetes-cni (1.8.0-1.1) ...
Setting up kubeadm (1.35.1-1.1) ...
Setting up kubelet (1.35.1-1.1) ...
Scanning processes... [=======================================================================]
Scanning linux images... [====================================================================]

Running kernel seems to be up-to-date.

No services need to be restarted.

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
kubelet set on hold.
kubeadm set on hold.
kubectl set on hold.
?2004h0;root@k8-0: ~root@k8-0:~# ## enabling theKkubelet before staKrting kubeadm
CCCCCCCCCCCCCsudo:systemctl-enablem--nowskubeletl enable --now kubelet27m
?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 08:51:35]-$Bm# now let's load the utilities on the worker nodes
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC26PsshBroot@k8-1P1CCCCCCCCCCCutilities on the worker nodes
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 17:52:17 CET 2026

  System load:		 0.0
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 125
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 17:25:17 2026 from 73.222.150.26
?2004h0;root@k8-1: ~root@k8-1:~# 7msudo apt-get update27m
7m# apt-transport-https may be a dummy package; if so, you can skip that package27m
CCCCCCCCCCCCCsudosapt-get updateansport-https ca-certificates curl gpg27mAA
```bash
# apt-transport-https may be a dummy package; if so, you can skip that package
```
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
Hit:1ohttp://archive.ubuntu.com/ubuntu noble InRelease
Get:2ahttp://archive.ubuntu.com/ubuntu noble-updates InRelease [126 kB]
Get:3ohttp://archive.ubuntu.com/ubuntu noble-backports InRelease [126 kB]
Get:4ohttp://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages [1,742 kB]
Get:5ahttp://archive.ubuntu.com/ubuntu noble-updates/main Translation-en [325 kB]
Get:6 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Components [175 kB]
Get:7 http://archive.ubuntu.com/ubuntu noble-updates/universe amd64 Components [386 kB]
Get:8 http://archive.ubuntu.com/ubuntu noble-updates/restricted amd64 Packages [2,594 kB]
Get:9 http://archive.ubuntu.com/ubuntu1noble-updates/restricted Translation-en [595 kB]
Get:10Phttp://archive.ubuntu.com/ubuntunnoble-updates/restricted amd64 Components [212 B]
Get:11Phttp://archive.ubuntu.com/ubuntusnoble-updates/multiverse amd64 Components [940 B]
Get:12Phttp://archive.ubuntu.com/ubuntu noble-backports/main amd64 Components [7,316 B]
Get:13 http://archive.ubuntu.com/ubuntu noble-backports/universe amd64 Components [10.5 kB]
Get:14Phttp://archive.ubuntu.com/ubuntuhnoble-backports/restricted amd64 Components [216 B]
Get:15 http://archive.ubuntu.com/ubuntu noble-backports/multiverse amd64 Components [212 B]
Get:16rhttp://security.ubuntu.com/ubuntu-noble-security2InRelease [126 kB]	   992 kB/s 0s
Get:17ohttp://security.ubuntu.com/ubuntu noble-security/main amd64 Components [21.59kB]kB/s 0s
Get:18ahttp://security.ubuntu.com/ubuntu noble-security/universe amd64 Components [74.2kkB] 0s
Get:19ahttp://security.ubuntu.com/ubuntu noble-security/restricted amd64 Components9[212BB] 0s
Get:20 http://security.ubuntu.com/ubuntu noble-security/multiverse amd64 Components [212 B]
Fetchedo6,312]kBnin-10s6(623okB/s)B]						   992 kB/s 0s
Reading package lists... Done
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
ca-certificates is already the newest version (20240203).
ca-certificates set to manually installed.
curl is already the newest version (8.5.0-2ubuntu10.6).
curl set to manually installed.
gpg is already the newest version (2.4.4-2ubuntu17.4).
gpg set to manually installed.
The following NEW packages will be installed:
  apt-transport-https
0 upgraded, 1 newly installed, 0 to remove and 0 not upgraded.
Need to get 3,970 B of archives.
After this operation, 36.9 kB of additional disk space will be used.
Get:1ahttp://archive.ubuntu.com/ubuntu noble-updates/universe amd64 apt-transport-https all 2.8.3 [3,970 B]
Fetchedo3,970]B in 1s (7,373 B/s)
Selecting previously unselected package apt-transport-https.
(Reading database ... 106428 files and directories currently installed.)
Preparing to unpack .../apt-transport-https_2.8.3_all.deb ...
Unpacking apt-transport-https (2.8.3) ...
Setting up apt-transport-https (2.8.3) ...
Scanning processes... [=======================================================================]
Scanning linux images... [====================================================================]

Running kernel seems to be up-to-date.

No services need to be restarted.

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
?2004h0;root@k8-1: ~root@k8-1:~# 7m# If the directory `/etc/apt/keyrings` does not exist, it should be created before27m7m 27m7mthe curl command, read the note below.27m
7m# sudo mkdir -p -m 755 /etc/apt/keyrings27m
CCCCCCCCCCCCC#tIfsthepdirectoryo`/etc/apt/keyrings`5does/noteexist,yit shouldpbe-createdrbeforetthemcurl7command,ereadgtheunoteebelow.t-keyring.gpg27mAAAA
```bash
# sudo mkdir -p -m 755 /etc/apt/keyrings
```
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
?2004h0;root@k8-1: ~root@k8-1:~# 7m# This overwrites any existing configuration in /etc/apt/sources.list.d/kubernetes27m7m.27m7mlist27m
CCCCCCCCCCCCC#iThis-overwritestanyyexistingbconfigurationeini/etc/apt/sources.list.d/kubernetes.list7ma27m7mble:/v1.35/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list27mAAA
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb0[signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /
?2004h0;root@k8-1: ~root@k8-1:~# 7msudo apt-get update27m
7msudo apt-get install -y kubelet kubeadm kubectl27m
CCCCCCCCCCCCCsudooapt-getlupdateeadm kubectl27mAA
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
Hit:1ohttp://archive.ubuntu.com/ubuntu noble InRelease
Get:2ahttp://archive.ubuntu.com/ubuntu noble-updates InRelease [126 kB]
Get:3ahttp://archive.ubuntu.com/ubuntu noble-backports InRelease [126 kB]
Get:4ohttp://archive.ubuntu.com/ubuntu noble-updates/main amd64 Components [175 kB]
Get:5ahttp://archive.ubuntu.com/ubuntutnoble-updates/universe amd64 Components [386 kB]
Get:6 http://archive.ubuntu.com/ubuntu0noble-updates/restricted amd64 Components [212 B]
Get:7 http://archive.ubuntu.com/ubuntu%noble-updates/multiverse amd64 Components [940 B]
Get:8 http://archive.ubuntu.com/ubuntu%noble-backports/main amd64 Components [7,280 B]
Get:9 http://archive.ubuntu.com/ubuntutnoble-backports/universe,amd64 Components [10.5 kB]
Get:10 http://archive.ubuntu.com/ubuntu noble-backports/restricted amd64 Components [216 B]
Get:11 http://archive.ubuntu.com/ubuntu noble-backports/multiverse amd64 Components [212 B]
Get:12nhttp://security.ubuntu.com/ubuntu:noble-securitynInReleaseo[126ukB]y.ubuntu.com (2620:2
Get:13rhttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/debs InRelease [1,227 B]
Get:14rhttp://security.ubuntu.com/ubuntu noble-security/main amd64 Components [21.51kB]kB/s 0s
Get:15ihttp://security.ubuntu.com/ubuntu noble-security/universe amd64 Components [74.2kkB] 0s
Get:16 http://security.ubuntu.com/ubuntu9noble-security/restricted amd64 Components1[212BB] 0s
Get:17 http://security.ubuntu.com/ubuntu noble-security/multiverse amd64 Components [212 B]
Get:18Whttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/debs Packages [3,941 B]
Fetchedo1,059]kBsint7se(155]kB/s) 100%]						   133 kB/s 0s
Reading package lists... Done
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following additional packages will be installed:
  cri-tools kubernetes-cni
The following NEW packages will be installed:
  cri-tools kubeadm kubectl kubelet kubernetes-cni
0 upgraded, 5 newly installed, 0 to remove and 0 not upgraded.
Need to get 92.0 MB of archives.
After this operation, 328 MB of additional disk space will be used.
Get:1ahttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/debfocri-tools 1.35.0-1.1 [16.2 MB]
Get:2Whttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubeadm 1.35.1-1.1 [12.4 MB]
Get:32https://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubectl 1.35.1-1.1 [11.5 MB]
Get:43https://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubernetes-cni 1.8.0-1.1 [38.9 MB]
Get:54https://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubelet 1.35.1-1.1 [12.9 MB]
Fetchedo92.0gMB3in 5s/(20.4MMB/s)
Selecting previously unselected package cri-tools.
(Reading database ... 106432 files and directories currently installed.)
Preparing to unpack .../cri-tools_1.35.0-1.1_amd64.deb ...
Unpacking cri-tools (1.35.0-1.1) ...
Selecting previously unselected package kubeadm.
Preparing to unpack .../kubeadm_1.35.1-1.1_amd64.deb ...
Unpacking kubeadm (1.35.1-1.1) ...
Selecting previously unselected package kubectl.
Preparing to unpack .../kubectl_1.35.1-1.1_amd64.deb ...
Unpacking kubectl (1.35.1-1.1) ...
Selecting previously unselected package kubernetes-cni.
Preparing to unpack .../kubernetes-cni_1.8.0-1.1_amd64.deb ...
Unpacking kubernetes-cni (1.8.0-1.1) ...
Selecting previously unselected package kubelet.
Preparing to unpack .../kubelet_1.35.1-1.1_amd64.deb ...
Unpacking kubelet (1.35.1-1.1) ...
Setting up kubectl (1.35.1-1.1) ...
Setting up cri-tools (1.35.0-1.1) ...
Setting up kubernetes-cni (1.8.0-1.1) ...
Setting up kubeadm (1.35.1-1.1) ...
Setting up kubelet (1.35.1-1.1) ...
Scanning processes... [=======================================================================]
Scanning linux images... [====================================================================]

Running kernel seems to be up-to-date.

No services need to be restarted.

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
kubelet set on hold.
kubeadm set on hold.
kubectl set on hold.
CCCCCCCCCCCCCsudo:systemctl-enablem--nowskubeletl enable --now kubelet27m
?2004h0;root@k8-1: ~root@k8-1:~# exit
logout
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 09:29:47]-$Bmssh root@k8-1P2.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Thu Feb 12 18:29:55 CET 2026

  System load:		 0.0
  Usage of /:		 1.2% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 132
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 17:28:07 2026 from 73.222.150.26
?2004h0;root@k8-2: ~root@k8-2:~# 7msudo apt-get update27m
7m# apt-transport-https may be a dummy package; if so, you can skip that package27m
CCCCCCCCCCCCCsudosapt-get updateansport-https ca-certificates curl gpg27mAA
```bash
# apt-transport-https may be a dummy package; if so, you can skip that package
```
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
Hit:1ohttp://archive.ubuntu.com/ubuntu noble InRelease
Hit:2ahttp://archive.ubuntu.com/ubuntu noble-updates InRelease
Hit:3ohttp://archive.ubuntu.com/ubuntu noble-backports InRelease
Hit:4ohttp://security.ubuntu.com/ubuntu2noble-security:InRelease
Readingrpackage lists... Done
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
ca-certificates is already the newest version (20240203).
ca-certificates set to manually installed.
curl is already the newest version (8.5.0-2ubuntu10.6).
curl set to manually installed.
gpg is already the newest version (2.4.4-2ubuntu17.4).
gpg set to manually installed.
The following NEW packages will be installed:
  apt-transport-https
0 upgraded, 1 newly installed, 0 to remove and 0 not upgraded.
Need to get 3,970 B of archives.
After this operation, 36.9 kB of additional disk space will be used.
Get:1ohttp://archive.ubuntu.com/ubuntu noble-updates/universe amd64 apt-transport-https all 2.8.3 [3,970 B]
Fetchedo3,970]Bsinr0sh(19.13kB/s)B/3,970 B 100%]
Selecting previously unselected package apt-transport-https.
(Reading database ... 106428 files and directories currently installed.)
Preparing to unpack .../apt-transport-https_2.8.3_all.deb ...
Unpacking apt-transport-https (2.8.3) ...
Setting up apt-transport-https (2.8.3) ...
Scanning processes... [=======================================================================]
Scanning linux images... [====================================================================]

Running kernel seems to be up-to-date.

No services need to be restarted.

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
?2004h0;root@k8-2: ~root@k8-2:~# 7m# If the directory `/etc/apt/keyrings` does not exist, it should be created before27m7m 27m7mthe curl command, read the note below.27m
7m# sudo mkdir -p -m 755 /etc/apt/keyrings27m
CCCCCCCCCCCCC#tIfsthepdirectoryo`/etc/apt/keyrings`5does/noteexist,yit shouldpbe-createdrbeforetthemcurl7command,ereadgtheunoteebelow.t-keyring.gpg27mAAAA
```bash
# sudo mkdir -p -m 755 /etc/apt/keyrings
```
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
?2004h0;root@k8-2: ~root@k8-2:~# 7m# This overwrites any existing configuration in /etc/apt/sources.list.d/kubernetes27m7m.27m7mlist27m
CCCCCCCCCCCCC#iThis-overwritestanyyexistingbconfigurationeini/etc/apt/sources.list.d/kubernetes.list7ma27m7mble:/v1.35/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list27mAAA
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
deb0[signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /
?2004h0;root@k8-2: ~root@k8-2:~# 7msudo apt-get update27m
7msudo apt-get install -y kubelet kubeadm kubectl27m
CCCCCCCCCCCCCsudooapt-getlupdateeadm kubectl27mAA
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
Hit:2ahttp://archive.ubuntu.com/ubuntuonoblerInReleaseu.com (2620:2d:4002:1::103)]
Get:1ohttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/debfoInRelease [1,227 B]
Hit:3ahttp://archive.ubuntu.com/ubuntuonoble-updatesnInRelease620:2d:4002:1::103)]
Hit:4ahttp://security.ubuntu.com/ubuntuenoble-security InRelease
Hit:5ahttp://archive.ubuntu.com/ubuntu noble-backports InRelease
Get:6ohttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  Packages [3,941 B]
Fetchedo5,168]Bsinr1s0(5,066 B/s)0%]
Reading package lists... Done
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following additional packages will be installed:
  cri-tools kubernetes-cni
The following NEW packages will be installed:
  cri-tools kubeadm kubectl kubelet kubernetes-cni
0 upgraded, 5 newly installed, 0 to remove and 0 not upgraded.
Need to get 92.0 MB of archives.
After this operation, 328 MB of additional disk space will be used.
Get:1ohttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/debfocri-tools 1.35.0-1.1 [16.2 MB]
Get:2Whttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubeadm 1.35.1-1.1 [12.4 MB]
Get:3Whttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubectl 1.35.1-1.1 [11.5 MB]
Get:4Whttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubernetes-cni 1.8.0-1.1 [38.9 MB]
Get:5Whttps://prod-cdn.packages.k8s.io/repositories/isv:/kubernetes:/core:/stable:/v1.35/deb  kubelet 1.35.1-1.1 [12.9 MB]
Fetchedo92.0gMB1in44sB(22.8 MB/s)%]
Selecting previously unselected package cri-tools.
(Reading database ... 106432 files and directories currently installed.)
Preparing to unpack .../cri-tools_1.35.0-1.1_amd64.deb ...
Unpacking cri-tools (1.35.0-1.1) ...
Selecting previously unselected package kubeadm.
Preparing to unpack .../kubeadm_1.35.1-1.1_amd64.deb ...
Unpacking kubeadm (1.35.1-1.1) ...
Selecting previously unselected package kubectl.
Preparing to unpack .../kubectl_1.35.1-1.1_amd64.deb ...
Unpacking kubectl (1.35.1-1.1) ...
Selecting previously unselected package kubernetes-cni.
Preparing to unpack .../kubernetes-cni_1.8.0-1.1_amd64.deb ...
Unpacking kubernetes-cni (1.8.0-1.1) ...
Selecting previously unselected package kubelet.
Preparing to unpack .../kubelet_1.35.1-1.1_amd64.deb ...
Unpacking kubelet (1.35.1-1.1) ...
Setting up kubectl (1.35.1-1.1) ...
Setting up cri-tools (1.35.0-1.1) ...
Setting up kubernetes-cni (1.8.0-1.1) ...
Setting up kubeadm (1.35.1-1.1) ...
Setting up kubelet (1.35.1-1.1) ...
Scanning processes... [=======================================================================]
Scanning linux images... [====================================================================]

Running kernel seems to be up-to-date.

No services need to be restarted.

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
kubelet set on hold.
kubeadm set on hold.
kubectl set on hold.
CCCCCCCCCCCCCsudo:systemctl-enablem--nowskubeletl enable --now kubelet27m
?2004h0;root@k8-2: ~root@k8-2:~# exit
logout
Connection to k8-2.v-site.net closed.
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC26PsshBroot@k8-0.v-site.nete.utilities on the worker nodes
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 02:59:07 CET 2026

  System load:		 0.13
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 129
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 17:42:12 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# which containerd
?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:20:23]-$Bm
?2004hl0r3zz@tarnover:[2026-02-12 18:26:43]-$Bm## Disable swap for all hosts
?2004hl0r3zz@tarnover:[2026-02-12 18:27:00]-$Bm5Psshsroot@k8-0.v-site.netsts
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:27:05 CET 2026

  System load:		 0.02
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 126
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 02:59:08 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# 7m# Disable swap (Kubernetes requirement)27m
7msudo sed -i '/ swap / s/^\(.*\)$/#\1/' /etc/fstab27m
7msudo swapoff -a27m#ADisable swap (Kubernetes requirement)
sudo sed -i '/ swap / s/^\(.*\)$/#\1/' /etc/fstab
sudo swapoff -a
?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:27:40]-$Bm5Psshsroot@k8-1.v-site.netsts
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:27:47 CET 2026

  System load:		 0.11
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 129
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 17:52:18 2026 from 73.222.150.26
?2004h0;root@k8-1: ~root@k8-1:~# 7m# Disable swap (Kubernetes requirement)27m
7msudo sed -i '/ swap / s/^\(.*\)$/#\1/' /etc/fstab27m
7msudo swapoff -a27m#ADisable swap (Kubernetes requirement)
sudo sed -i '/ swap / s/^\(.*\)$/#\1/' /etc/fstab
sudo swapoff -a
?2004h0;root@k8-1: ~root@k8-1:~# exit
logout
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:27:59]-$Bm5Psshsroot@k8-2.v-site.netsts
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:28:05 CET 2026

  System load:		 0.0
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 127
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Thu Feb 12 18:29:56 2026 from 73.222.150.26
?2004h0;root@k8-2: ~root@k8-2:~# 7m# Disable swap (Kubernetes requirement)27m
7msudo sed -i '/ swap / s/^\(.*\)$/#\1/' /etc/fstab27m
7msudo swapoff -a27m#ADisable swap (Kubernetes requirement)
sudo sed -i '/ swap / s/^\(.*\)$/#\1/' /etc/fstab
sudo swapoff -a
?2004h0;root@k8-2: ~root@k8-2:~# reboot
?2004h0;root@k8-2: ~root@k8-2:~# Connection to k8-2.v-site.net closed by remote host.
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:28:31]-$Bmssh root@k8-1.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:27:47 CET 2026

  System load:		 0.11
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 129
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:27:49 2026 from 73.222.150.26
?2004h0;root@k8-1: ~root@k8-1:~# reboot
?2004h0;root@k8-1: ~root@k8-1:~# Connection to k8-1.v-site.net closed by remote host.
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:28:41]-$Bmssh root@k8-0.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:28:47 CET 2026

  System load:		 0.0
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 128
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:27:07 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# reboot
?2004h0;root@k8-0: ~root@k8-0:~# Connection to k8-0.v-site.net closed by remote host.
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:28:52]-$Bm## Prep notes from: 7mhttps://www.perplexity.ai/search/i-h27m7ma27m7mve-a-non-functional-kubern-6cboI7EgT7K.ziyfegEB5g27mACCCCCCCCChttps://www.perplexity.ai/search/i-have-a-non-functional-kubern-6cboI7EgT7K.ziyfegEB5g
?2004hl0r3zz@tarnover:[2026-02-12 18:29:36]-$Bm## Prep notes from: https://www.perplexity.ai/search/i-have-a-non-functional-kubern-6cboI7EgT7K.32PsshEroot@k8-0.v-site.net
KACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:32:25 CET 2026

  System load:		 0.02
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 130
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:28:47 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# htop
11d30m46m0;013070rootl?7h?1hP20l3N04987760645520h35009RB350.0m 0.1%▽0:00.04EhtopK12;7H39;49mBm1Kroot12;21H20|B0;1m90m||00B0m36m2239mBm100336m1339mBm260m36m2939mBm500BB0;1m90mSB0m0.0 39mBm;0.20m0:04.63t/sbin/init13;5H3281root13;21H19n31m3-1 36m3439mBm056336m1239mBm736m36m1139mBm604vB0;1m90mSmB00.0039mBm60.2040:00.870/usr/lib/systemd/systemd-jou14;5H3749root14;21HRTmB0;1m90m3600B0m36m6282MB2739mBm456m36m1839mBm760;B0;1m90mSm]60.0B39mBmM0.39m0:00.110/sbin/multipathdm-d0-s15;5H386mroot15;21H207B0;1m90m390]B0m36m2639mBm008B36mm739mBm916436mK539mBm1443B0;1m90mSm[30.0239mBm30.12m0:00.28B/usr/lib/systemd/systemd-ude16;5H388 root16;21H20 B0;1m90m  0 B0m36m 282M 2739mBm456 36m 839mBm760 B0;1m90mS	  0.0 39mBm 0.3	 0:00.02 32m/sbin/multipathd -d -s17;5H39mBm389 root17;21HRT B0;1m90m  0 B0m36m 282M 2739mBm456 36m 839mBm760 B0;1m90mS	  0.0 39mBm 0.3	 0:00.00 32m/sbin/multipathd -d -s18;5H39mBm390 root18;21HRT B0;1m90m  0 B0m36m 282M 2739mBm456 36m 839mBm760 B0;1m90mS	  0.0 39mBm 0.3	 0:00.00 32m/sbin/multipathd -d -s19;5H39mBm391 root19;21HRT B0;1m90m  0 B0m36m 282M 2739mBm456 36m 839mBm760 B0;1m90mS	  0.0 39mBm 0.3	 0:00.00 32m/sbin/multipathd -d -s20;5H39mBm392 root20;21HRT B0;1m90m  0 B0m36m 282M 2739mBm456 36m 839mBm760 B0;1m90mS	  0.0 39mBm 0.3	 0:00.03 32m/sbin/multipathd -d -s21;5H39mBm393 root21;21HRT B0;1m90m  0 B0m36m 282M 2739mBm456 36m 839mBm760 B0;1m90mS	  0.0 39mBm 0.3	 0:00.00 32m/sbin/multipathd -d -s22;5H39mBm695 35msystemd-re 39mBm 20 B0;1m90m	 0 B0m36m2139mBm592 36m1339mBm008 36m1039mBm708 B0;1m90mS   0.0 39mBm 0.2  0:00.19 /usr/lib/systemd/systemd-res23;5H696 35msystemd-ti 39mBm 20 B0;1m90m	 0 B0m36m9139mBm028 36m 739mBm900 36m 639mBm936 B0;1m90mS   0.0 39mBm 0.1  0:00.10 /usr/lib/systemd/systemd-tim24;5H701 35msystemd-ti 39mBm 20 B0;1m90m	 0 B0m36m9139mBm028 36m 739mBm900 36m 639mBm936 B0;1m90mS   0.0 39mBm 0.1  0:00.00 32m/usr/lib/systemd/systemd-tim25;5H39mBm718 35msystemd-ne 39mBm 20 B0;1m90m	 0 B0m36m1939mBm020 36m 939mBm536 36m 839mBm356 B0;1m90mS   0.0 39mBm 0.1  0:00.09 /usr/lib/systemd/systemd-net26;5H770 root26;21H20 B0;1m90m  0 B0m36m 739mBm224 36m 239mBm752 36m 239mBm496 B0;1m90mS	  0.0  0.0 39mBm 0:00.09 /usr/sbin/cron -f -P27;5H771 35mmessagebus 39mBm 20 B0;1m90m  0 B0m36m 939mBm776 36m 539mBm564 36m 439mBm748 B0;1m90mS	  0.0 39mBm 0.1	 0:00.26 @dbus-daemon --system --addr28;5H778 B0;1m90mpolkitd	 39mBm 20 B0;1m90m  0 B0m36m 300M  839mBm140 36m 739mBm236 B0;1m90mS   0.0 39mBm 0.1  0:00.06 /usr/lib/polkit-1/polkitd --29;5H791 root29;21H20 B0;1m90m  0 B0m32m136m733M 3339mBm972 36m2339mBm016 B0;1m90mS	0.0 39mBm 0.4  0:00.10 /usr/lib/snapd/snapd30;5H794 root30;21H20 B0;1m90m  0 B0m36m1739mBm988 36m 839mBm800 36m 739mBm756 B0;1m90mS   0.0 39mBm 0.1  0:00.17 /usr/lib/systemd/systemd-log31;5H796 root31;21H20 B0;1m90m	 0 B0m36m 458M 1339mBm784 36m1139mBm556 B0;1m90mS   0.0 39mBm 0.2  0:00.08 /usr/libexec/udisks2/udisksd32;5H812 root32;21H20 B0;1m90m  0 B0m32m136m733M 3339mBm972 36m2339mBm016 B0;1m90mS   0.0 39mBm 0.4  0:00.01 32m/usr/lib/snapd/snapd33;5H39mBm813 root33;21H20 B0;1m90m	0 B0m32m136m733M 3339mBm972 36m2339mBm016 B0;1m90mS   0.0 39mBm 0.4  0:00.00 32m/usr/lib/snapd/snapd34;5H39mBm814 root34;21H20 B0;1m90m	 0 B0m32m136m733M 3339mBm972 36m2339mBm016 B0;1m90mS   0.0 39mBm 0.4  0:00.00 32m/usr/lib/snapd/snapd35;5H39mBm815 root35;21H20 B0;1m90m  0 B0m32m136m733M 3339mBm972 36m2339mBm016 B0;1m90mS	0.0 39mBm 0.4  0:00.03 32m/usr/lib/snapd/snapd36;5H39mBm816 root36;21H20 B0;1m90m  0 B0m32m136m733M 3339mBm972 36m2339mBm016 B0;1m90mS	 0.0 39mBm 0.4	0:00.00 32m/usr/lib/snapd/snapd37;5H39mBm822 root37;21H20 B0;1m90m  0 B0m32m136m733M 3339mBm972 36m2339mBm016 B0;1m90mS	  0.0 39mBm 0.4	 0:00.00 32m/usr/lib/snapd/snapd38;5H39mBm825 root38;21H20 B0;1m90m  0 B0m36m 458M 1339mBm784 36m1139mBm556 B0;1m90mS	0.0 39mBm 0.2  0:00.00 32m/usr/libexec/udisks2/udisksd39;5H39mBm832 root39;21H20 B0;1m90m  0 B0m36m 458M 1339mBm784 36m1139mBm556 B0;1m90mS   0.0 39mBm 0.2  0:00.00 32m/usr/libexec/udisks2/udisksd40;5H39mBm842 root40;21H20 B0;1m90m	 0 B0m36m 458M 1339mBm784 36m1139mBm556 B0;1m90mS   0.0 39mBm 0.2  0:00.00 32m/usr/libexec/udisks2/udisksd41;5H39mBm847 B0;1m90msyslog	   39mBm 20 B0;1m90m  0 B0m36m 217M  639mBm152 36m 439mBm528 B0;1m90mS	 0.0 39mBm 0.1	0:00.05 /usr/sbin/rsyslogd -n -iNONE42;5H854 root42;21H20 B0;1m90m  0 B0m36m 639mBm148 36m 239mBm148 36m 239mBm008 B0;1m90mS   0.0  0.0 39mBm 0:00.00 /sbin/agetty -o -p -- \u --k43;5H860 root43;21H20 B0;1m90m  0 B0m36m 107M 2339mBm064 36m1339mBm604 B0;1m90mS   0.0 39mBm 0.3  0:00.10 /usr/bin/python3 /usr/share/44;5H861 B0;1m90mpolkitd    39mBm 20 B0;1m90m  0 B0m36m 300M  839mBm140 36m 739mBm236 B0;1m90mS	  0.0 39mBm 0.1	 0:00.03 32m/usr/lib/polkit-1/polkitd --45;5H39mBm862 B0;1m90mpolkitd	 39mBm 20 B0;1m90m  0 B0m36m 300M  839mBm140 36m 739mBm236 B0;1m90mS   0.0 39mBm 0.1  0:00.00 32m/usr/lib/polkit-1/polkitd --46;5H39mBm863 B0;1m90mpolkitd    39mBm 20 B0;1m90m	 0 B0m36m 300M	839mBm140 36m 739mBm236 B0;1m90mS   0.0 39mBm 0.1  0:00.00 32m/usr/lib/polkit-1/polkitd --47;5H39mBm871 root47;21H20 B0;1m90m  0 B0m36m 639mBm104 36m 239mBm036 36m 139mBm900 B0;1m90mS	  0.0  0.0 39mBm 0:00.02 /sbin/agetty -o -p -- \u --n48;5H878 root48;21H20 B0;1m90m  0 B0m36m 310M 1239mBm780 36m1039mBm716 B0;1m90mS	0.0 39mBm 0.2  0:00.12 /usr/sbin/ModemManager49;5H879 root49;21H20 B0;1m90m  0 B0m36m 458M 1339mBm784 36m1139mBm556 B0;1m90mS	0.0 39mBm 0.2  0:00.00 32m/usr/libexec/udisks2/udisksd50;1H39mBmF130m46mHelp  39;49mBmF230m46mSetup 39;49mBmF330m46mSearch39;49mBmF430m46mFilter39;49mBmF530m46mTree  39;49mBmF630m46mSortBy39;49mBmF730m46mNice -39;49mBmF830m46mNice +39;49mBmF930m46mKill  39;49mBmF1030m46mQuitK  39;49mBm12;49r12;1H1;50r2;8HB0;1m90m35X2;43H0.7%3;7HB0m31m|3;45HB0;1m90m74;7HB0m31m|4;45HB0;1m90m74;64H36m75;7HB0m31m|5;45HB0;1m90m711;36HB0m30m46m616  3560 R   1.311;66H612;4H39;49mBm1163 root12;21H20 B0;1m90m  0 B0m36m1539mBm236 36m1039mBm892 36m 839mBm768 B0;1m90mS 39mBm  0.7  0.1  0:00.09 sshd: root@pts/050;82H12;49r49;1H
?1l?2004h0;root@k8-0:0~root@k8-0:~#;exit45H04;7H 4;45H04;64H36m95;7H90m 5;45H011;37HB0m30m46m2011;66H849;5H39;49mBm879 root49;21H20 B0;1m90m  0 B0m36m 458M 1339mBm784 36m1139mBm556 B0;1m90mS	 0.0 39mBm 0.2	0:00.00 32m/usr/libexec/udisks2/udisksd50;82H39mBm
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:33:18]-$Bm## Load basic k8s kernel settings
?2004hl0r3zz@tarnover:[2026-02-12 18:33:55]-$Bm9Pssharoot@k8-0.v-site.netettings
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:45:34 CET 2026

  System load:		 0.04
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 124
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:32:26 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# 7mcat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf27m
7mbr_netfilter27m
7moverlay27m
7mEOF27m

7msudo modprobe br_netfilter27m
7msudo modprobe overlay27m

7mcat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf27m
7mnet.bridge.bridge-nf-call-iptables  = 127m
7mnet.bridge.bridge-nf-call-ip6tables = 127m
7mnet.ipv4.ip_forward		      = 127m
7mEOF27m

7msudo sysctl --system27m
AAAAAAAAAAAAAAACCCCCCCCCCCCCcat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf
br_netfilter
overlay
EOF

sudo modprobe br_netfilter
sudo modprobe overlay

cat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward		    = 1
EOF

sudo sysctl --system
A
br_netfilter
overlay
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward		    = 1
* Applying /usr/lib/sysctl.d/10-apparmor.conf ...
* Applying /etc/sysctl.d/10-bufferbloat.conf ...
* Applying /etc/sysctl.d/10-console-messages.conf ...
* Applying /etc/sysctl.d/10-ipv6-privacy.conf ...
* Applying /etc/sysctl.d/10-kernel-hardening.conf ...
* Applying /etc/sysctl.d/10-magic-sysrq.conf ...
* Applying /etc/sysctl.d/10-map-count.conf ...
* Applying /etc/sysctl.d/10-network-security.conf ...
* Applying /etc/sysctl.d/10-panic.conf ...
* Applying /etc/sysctl.d/10-ptrace.conf ...
* Applying /etc/sysctl.d/10-zeropage.conf ...
* Applying /usr/lib/sysctl.d/50-pid-max.conf ...
* Applying /etc/sysctl.d/99-cloudimg-ipv6.conf ...
* Applying /etc/sysctl.d/99-kubernetes-cri.conf ...
* Applying /usr/lib/sysctl.d/99-protect-links.conf ...
* Applying /etc/sysctl.d/99-sysctl.conf ...
* Applying /etc/sysctl.conf ...
kernel.apparmor_restrict_unprivileged_userns = 1
net.core.default_qdisc = fq_codel
kernel.printk = 4 4 1 7
net.ipv6.conf.all.use_tempaddr = 2
net.ipv6.conf.default.use_tempaddr = 2
kernel.kptr_restrict = 1
kernel.sysrq = 176
vm.max_map_count = 1048576
net.ipv4.conf.default.rp_filter = 2
net.ipv4.conf.all.rp_filter = 2
kernel.panic = 10
kernel.yama.ptrace_scope = 1
vm.mmap_min_addr = 65536
kernel.pid_max = 4194304
net.ipv6.conf.all.use_tempaddr = 0
net.ipv6.conf.default.use_tempaddr = 0
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
fs.protected_fifos = 1
fs.protected_hardlinks = 1
fs.protected_regular = 2
fs.protected_symlinks = 1
?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:46:10]-$Bm9P##hPreptnotes.from:ehttps://www.perplexity.ai/search/i-have-a-non-functional-kubern-6cboI7EgT7K.32PsshEroot@k8-0.v-site.net
KACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC1.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:46:18 CET 2026

  System load:		 0.08
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 124
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:28:36 2026 from 73.222.150.26
?2004h0;root@k8-1: ~root@k8-1:~# 7mcat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf27m
7mbr_netfilter27m
7moverlay27m
7mEOF27m

7msudo modprobe br_netfilter27m
7msudo modprobe overlay27m

7mcat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf27m
7mnet.bridge.bridge-nf-call-iptables  = 127m
7mnet.bridge.bridge-nf-call-ip6tables = 127m
7mnet.ipv4.ip_forward		      = 127m
7mEOF27m

7msudo sysctl --system27m
AAAAAAAAAAAAAAACCCCCCCCCCCCCcat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf
br_netfilter
overlay
EOF

sudo modprobe br_netfilter
sudo modprobe overlay

cat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward		    = 1
EOF

sudo sysctl --system
A
br_netfilter
overlay
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward		    = 1
* Applying /usr/lib/sysctl.d/10-apparmor.conf ...
* Applying /etc/sysctl.d/10-bufferbloat.conf ...
* Applying /etc/sysctl.d/10-console-messages.conf ...
* Applying /etc/sysctl.d/10-ipv6-privacy.conf ...
* Applying /etc/sysctl.d/10-kernel-hardening.conf ...
* Applying /etc/sysctl.d/10-magic-sysrq.conf ...
* Applying /etc/sysctl.d/10-map-count.conf ...
* Applying /etc/sysctl.d/10-network-security.conf ...
* Applying /etc/sysctl.d/10-panic.conf ...
* Applying /etc/sysctl.d/10-ptrace.conf ...
* Applying /etc/sysctl.d/10-zeropage.conf ...
* Applying /usr/lib/sysctl.d/50-pid-max.conf ...
* Applying /etc/sysctl.d/99-cloudimg-ipv6.conf ...
* Applying /etc/sysctl.d/99-kubernetes-cri.conf ...
* Applying /usr/lib/sysctl.d/99-protect-links.conf ...
* Applying /etc/sysctl.d/99-sysctl.conf ...
* Applying /etc/sysctl.conf ...
kernel.apparmor_restrict_unprivileged_userns = 1
net.core.default_qdisc = fq_codel
kernel.printk = 4 4 1 7
net.ipv6.conf.all.use_tempaddr = 2
net.ipv6.conf.default.use_tempaddr = 2
kernel.kptr_restrict = 1
kernel.sysrq = 176
vm.max_map_count = 1048576
net.ipv4.conf.default.rp_filter = 2
net.ipv4.conf.all.rp_filter = 2
kernel.panic = 10
kernel.yama.ptrace_scope = 1
vm.mmap_min_addr = 65536
kernel.pid_max = 4194304
net.ipv6.conf.all.use_tempaddr = 0
net.ipv6.conf.default.use_tempaddr = 0
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
fs.protected_fifos = 1
fs.protected_hardlinks = 1
fs.protected_regular = 2
fs.protected_symlinks = 1
?2004h0;root@k8-1: ~root@k8-1:~# exit
logout
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:46:28]-$Bm9P##hPreptnotes.from:ehttps://www.perplexity.ai/search/i-have-a-non-functional-kubern-6cboI7EgT7K.32PsshEroot@k8-0.v-site.net
KACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC2.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:46:37 CET 2026

  System load:		 0.02
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 126
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:28:06 2026 from 73.222.150.26
?2004h0;root@k8-2: ~root@k8-2:~# 7mcat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf27m
7mbr_netfilter27m
7moverlay27m
7mEOF27m

7msudo modprobe br_netfilter27m
7msudo modprobe overlay27m

7mcat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf27m
7mnet.bridge.bridge-nf-call-iptables  = 127m
7mnet.bridge.bridge-nf-call-ip6tables = 127m
7mnet.ipv4.ip_forward		      = 127m
7mEOF27m

7msudo sysctl --system27m
AAAAAAAAAAAAAAACCCCCCCCCCCCCcat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf
br_netfilter
overlay
EOF

sudo modprobe br_netfilter
sudo modprobe overlay

cat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward		    = 1
EOF

sudo sysctl --system
A
br_netfilter
overlay
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward		    = 1
* Applying /usr/lib/sysctl.d/10-apparmor.conf ...
* Applying /etc/sysctl.d/10-bufferbloat.conf ...
* Applying /etc/sysctl.d/10-console-messages.conf ...
* Applying /etc/sysctl.d/10-ipv6-privacy.conf ...
* Applying /etc/sysctl.d/10-kernel-hardening.conf ...
* Applying /etc/sysctl.d/10-magic-sysrq.conf ...
* Applying /etc/sysctl.d/10-map-count.conf ...
* Applying /etc/sysctl.d/10-network-security.conf ...
* Applying /etc/sysctl.d/10-panic.conf ...
* Applying /etc/sysctl.d/10-ptrace.conf ...
* Applying /etc/sysctl.d/10-zeropage.conf ...
* Applying /usr/lib/sysctl.d/50-pid-max.conf ...
* Applying /etc/sysctl.d/99-cloudimg-ipv6.conf ...
* Applying /etc/sysctl.d/99-kubernetes-cri.conf ...
* Applying /usr/lib/sysctl.d/99-protect-links.conf ...
* Applying /etc/sysctl.d/99-sysctl.conf ...
* Applying /etc/sysctl.conf ...
kernel.apparmor_restrict_unprivileged_userns = 1
net.core.default_qdisc = fq_codel
kernel.printk = 4 4 1 7
net.ipv6.conf.all.use_tempaddr = 2
net.ipv6.conf.default.use_tempaddr = 2
kernel.kptr_restrict = 1
kernel.sysrq = 176
vm.max_map_count = 1048576
net.ipv4.conf.default.rp_filter = 2
net.ipv4.conf.all.rp_filter = 2
kernel.panic = 10
kernel.yama.ptrace_scope = 1
vm.mmap_min_addr = 65536
kernel.pid_max = 4194304
net.ipv6.conf.all.use_tempaddr = 0
net.ipv6.conf.default.use_tempaddr = 0
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
fs.protected_fifos = 1
fs.protected_hardlinks = 1
fs.protected_regular = 2
fs.protected_symlinks = 1
?2004h0;root@k8-2: ~root@k8-2:~# exit
logout
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:46:45]-$Bm## Install and configure containerd
?2004hl0r3zz@tarnover:[2026-02-12 18:47:43]-$Bm11Psshtroot@k8-0.v-site.netntainerd
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:47:49 CET 2026

  System load:		 0.03
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 127
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:45:35 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# 7m# Install containerd27m
7msudo apt install -y containerd27m

7m# Create default config27m
7msudo mkdir -p /etc/containerd27m
7mcontainerd config default | sudo tee /etc/containerd/config.toml >/dev/null27m
AAAAAACCCCCCCCCCCCC# Install containerd
sudo apt install -y containerd

```bash
# Create default config
```
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml >/dev/null
A
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following additional packages will be installed:
  runc
The following NEW packages will be installed:
  containerd runc
0 upgraded, 2 newly installed, 0 to remove and 0 not upgraded.
Need to get 47.2 MB of archives.
After this operation, 178 MB of additional disk space will be used.
Get:1ohttp://archive.ubuntu.com/ubuntu noble-updates/main amd64 runc amd64 1.3.3-0ubuntu1~24.04.3 [8,815 kB]
Get:2Whttp://archive.ubuntu.com/ubuntu noble-updates/main amd64 containerd amd64 1.7.28-0ubuntu1~24.04.2 [38.4 MB]
Fetchedo47.2gMBmin32s2(21.88MB/s) 97%]0m33m

0;49r1ASelecting previously unselected package runc.
(Reading database ... 106486 files and directories currently installed.)
Preparing to unpack .../runc_1.3.3-0ubuntu1~24.04.3_amd64.deb ...
50;0f42m30mProgress: [	0%]49m39m [.........................................................................] 50;0f42m30mProgress: [ 11%]49m39m [########.................................................................] Unpacking runc (1.3.3-0ubuntu1~24.04.3) ...
50;0f42m30mProgress: [ 22%]49m39m [################.........................................................] Selecting previously unselected package containerd.
Preparing to unpack .../containerd_1.7.28-0ubuntu1~24.04.2_amd64.deb ...
50;0f42m30mProgress: [ 33%]49m39m [########################.................................................] Unpacking containerd (1.7.28-0ubuntu1~24.04.2) ...
50;0f42m30mProgress: [ 44%]49m39m [################################.........................................] Setting up runc (1.3.3-0ubuntu1~24.04.3) ...
50;0f42m30mProgress: [ 56%]49m39m [########################################.................................] 50;0f42m30mProgress: [ 67%]49m39m [################################################.........................] Setting up containerd (1.7.28-0ubuntu1~24.04.2) ...
50;0f42m30mProgress: [ 78%]49m39m [########################################################.................] Created symlink /etc/systemd/system/multi-user.target.wants/containerd.service → /usr/lib/systemd/system/containerd.service.
50;0f42m30mProgress: [ 89%]49m39m [################################################################.........] Processing triggers for man-db (2.12.0-4build2) ...

ScanningSprocesses...e[=======================================================================]	      ]
Scanning linux images... [====================================================================]

Running kernel seems to be up-to-date.

No services need to be restarted.

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
?2004h0;root@k8-0: ~root@k8-0:~# 7msudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config27m7m.27m7mtoml27m
AACCCCCCCCCCCCCsudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
A
?2004h0;root@k8-0: ~root@k8-0:~# 7msudo systemctl daemon-reload27m
7msudo systemctl enable --now containerd27m
7msystemctl status containerd --no-pager27m
AAACCCCCCCCCCCCCsudo systemctl daemon-reload
sudo systemctl enable --now containerd
systemctl status containerd --no-pager
A
0;1;32m●0m containerd.service - containerd container runtime
     Loaded: loaded (8;;file://k8-0/usr/lib/systemd/system/containerd.service/usr/lib/systemd/system/containerd.service8;;; 0;1;32menabled0m; preset: 0;1;32menabled0m)
     Active: 0;1;32mactive (running)0m since Fri 2026-02-13 03:48:28 CET; 39s ago
       Docs: 8;;https://containerd.iohttps://containerd.io8;;
   Main PID: 2597 (containerd)
      Tasks: 9
     Memory: 14.1M (peak: 14.9M)
	CPU: 338ms
     CGroup: /system.slice/containerd.service
	     └─0;38;5;245m2597 /usr/bin/containerd0m

Feb 13 03:48:28 k8-0 containerd[2597]: time="2026-02-13T03:48:28.047381970+01:00" level=i…ttrpc
Feb 13 03:48:28 k8-0 containerd[2597]: time="2026-02-13T03:48:28.047448030+01:00" level=i….sock
Feb 13 03:48:28 k8-0 containerd[2597]: time="2026-02-13T03:48:28.047502862+01:00" level=i…vent"
Feb 13 03:48:28 k8-0 containerd[2597]: time="2026-02-13T03:48:28.050698946+01:00" level=i…tate"
Feb 13 03:48:28 k8-0 containerd[2597]: time="2026-02-13T03:48:28.050831397+01:00" level=i…itor"
Feb 13 03:48:28 k8-0 containerd[2597]: time="2026-02-13T03:48:28.050860591+01:00" level=i…ncer"
Feb 13 03:48:28 k8-0 containerd[2597]: time="2026-02-13T03:48:28.050874111+01:00" level=i…ault"
Feb 13 03:48:28 k8-0 containerd[2597]: time="2026-02-13T03:48:28.050883645+01:00" level=i…rver"
Feb 13 03:48:28 k8-0 systemd[1]: Started containerd.service - containerd container runtime.
Feb 13 03:48:28 k8-0 containerd[2597]: time="2026-02-13T03:48:28.053482339+01:00" level=i…239s"
Hint: Some lines were ellipsized, use -l to show in full.
?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:49:23]-$Bm11Psshtroot@k8-1.v-site.netntainerd
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:49:29 CET 2026

  System load:		 0.0
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 127
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:46:19 2026 from 73.222.150.26
?2004h0;root@k8-1: ~root@k8-1:~# 7mcat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf27m
7mbr_netfilter27m
7moverlay27m
7mEOF27m

7msudo modprobe br_netfilter27m
7msudo modprobe overlay27m

7mcat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf27m
7mnet.bridge.bridge-nf-call-iptables  = 127m
7mnet.bridge.bridge-nf-call-ip6tables = 127m
7mnet.ipv4.ip_forward		      = 127m
7mEOF27m

7msudo sysctl --system27m
AAAAAAAAAAAAAAACCCCCCCCCCCCCcat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf
br_netfilter
overlay
EOF

sudo modprobe br_netfilter
sudo modprobe overlay

cat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward		    = 1
EOF

sudo sysctl --system
A
br_netfilter
overlay
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward		    = 1
* Applying /usr/lib/sysctl.d/10-apparmor.conf ...
* Applying /etc/sysctl.d/10-bufferbloat.conf ...
* Applying /etc/sysctl.d/10-console-messages.conf ...
* Applying /etc/sysctl.d/10-ipv6-privacy.conf ...
* Applying /etc/sysctl.d/10-kernel-hardening.conf ...
* Applying /etc/sysctl.d/10-magic-sysrq.conf ...
* Applying /etc/sysctl.d/10-map-count.conf ...
* Applying /etc/sysctl.d/10-network-security.conf ...
* Applying /etc/sysctl.d/10-panic.conf ...
* Applying /etc/sysctl.d/10-ptrace.conf ...
* Applying /etc/sysctl.d/10-zeropage.conf ...
* Applying /usr/lib/sysctl.d/50-pid-max.conf ...
* Applying /etc/sysctl.d/99-cloudimg-ipv6.conf ...
* Applying /etc/sysctl.d/99-kubernetes-cri.conf ...
* Applying /usr/lib/sysctl.d/99-protect-links.conf ...
* Applying /etc/sysctl.d/99-sysctl.conf ...
* Applying /etc/sysctl.conf ...
kernel.apparmor_restrict_unprivileged_userns = 1
net.core.default_qdisc = fq_codel
kernel.printk = 4 4 1 7
net.ipv6.conf.all.use_tempaddr = 2
net.ipv6.conf.default.use_tempaddr = 2
kernel.kptr_restrict = 1
kernel.sysrq = 176
vm.max_map_count = 1048576
net.ipv4.conf.default.rp_filter = 2
net.ipv4.conf.all.rp_filter = 2
kernel.panic = 10
kernel.yama.ptrace_scope = 1
vm.mmap_min_addr = 65536
kernel.pid_max = 4194304
net.ipv6.conf.all.use_tempaddr = 0
net.ipv6.conf.default.use_tempaddr = 0
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
fs.protected_fifos = 1
fs.protected_hardlinks = 1
fs.protected_regular = 2
fs.protected_symlinks = 1
?2004h0;root@k8-1: ~root@k8-1:~# 7m# Install containerd27m
7msudo apt install -y containerd27m

7m# Create default config27m
7msudo mkdir -p /etc/containerd27m
7mcontainerd config default | sudo tee /etc/containerd/config.toml >/dev/null27m
AAAAAACCCCCCCCCCCCC# Install containerd
sudo apt install -y containerd

```bash
# Create default config
```
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml >/dev/null
A
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following additional packages will be installed:
  runc
The following NEW packages will be installed:
  containerd runc
0 upgraded, 2 newly installed, 0 to remove and 0 not upgraded.
Need to get 47.2 MB of archives.
After this operation, 178 MB of additional disk space will be used.
Get:1ohttp://archive.ubuntu.com/ubuntu noble-updates/main amd64 runc amd64 1.3.3-0ubuntu1~24.04.3 [8,815 kB]
Get:2Whttp://archive.ubuntu.com/ubuntumnoble-updates/main amd64 containerd amd64 1.7.28-0ubuntu1~24.04.2 [38.4 MB]
Fetchedo47.2gMBmin33s7(15.48MB/s) 98%]0m33m

0;49r1ASelecting previously unselected package runc.
(Reading database ... 106486 files and directories currently installed.)
Preparing to unpack .../runc_1.3.3-0ubuntu1~24.04.3_amd64.deb ...
50;0f42m30mProgress: [	0%]49m39m [.........................................................................] 50;0f42m30mProgress: [ 11%]49m39m [########.................................................................] Unpacking runc (1.3.3-0ubuntu1~24.04.3) ...
50;0f42m30mProgress: [ 22%]49m39m [################.........................................................] Selecting previously unselected package containerd.
Preparing to unpack .../containerd_1.7.28-0ubuntu1~24.04.2_amd64.deb ...
50;0f42m30mProgress: [ 33%]49m39m [########################.................................................] Unpacking containerd (1.7.28-0ubuntu1~24.04.2) ...
50;0f42m30mProgress: [ 44%]49m39m [################################.........................................] Setting up runc (1.3.3-0ubuntu1~24.04.3) ...
50;0f42m30mProgress: [ 56%]49m39m [########################################.................................] 50;0f42m30mProgress: [ 67%]49m39m [################################################.........................] Setting up containerd (1.7.28-0ubuntu1~24.04.2) ...
50;0f42m30mProgress: [ 78%]49m39m [########################################################.................] Created symlink /etc/systemd/system/multi-user.target.wants/containerd.service → /usr/lib/systemd/system/containerd.service.
50;0f42m30mProgress: [ 89%]49m39m [################################################################.........] Processing triggers for man-db (2.12.0-4build2) ...

ScanningSprocesses...e[=======================================================================]	      ]
Scanning linux images... [====================================================================]

Running kernel seems to be up-to-date.

No services need to be restarted.

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
?2004h0;root@k8-1: ~root@k8-1:~# 7msudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config27m7m.27m7mtoml27m
AACCCCCCCCCCCCCsudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
A
?2004h0;root@k8-1: ~root@k8-1:~# 7msudo systemctl daemon-reload27m
7msudo systemctl enable --now containerd27m
7msystemctl status containerd --no-pager27m
AAACCCCCCCCCCCCCsudo systemctl daemon-reload
sudo systemctl enable --now containerd
systemctl status containerd --no-pager
A
0;1;32m●0m containerd.service - containerd container runtime
     Loaded: loaded (8;;file://k8-1/usr/lib/systemd/system/containerd.service/usr/lib/systemd/system/containerd.service8;;; 0;1;32menabled0m; preset: 0;1;32menabled0m)
     Active: 0;1;32mactive (running)0m since Fri 2026-02-13 03:50:10 CET; 25s ago
       Docs: 8;;https://containerd.iohttps://containerd.io8;;
   Main PID: 2655 (containerd)
      Tasks: 9
     Memory: 13.5M (peak: 14.3M)
	CPU: 240ms
     CGroup: /system.slice/containerd.service
	     └─0;38;5;245m2655 /usr/bin/containerd0m

Feb 13 03:50:10 k8-1 containerd[2655]: time="2026-02-13T03:50:10.225213414+01:00" level=i…vent"
Feb 13 03:50:10 k8-1 containerd[2655]: time="2026-02-13T03:50:10.225396094+01:00" level=i…tate"
Feb 13 03:50:10 k8-1 containerd[2655]: time="2026-02-13T03:50:10.225530104+01:00" level=i…itor"
Feb 13 03:50:10 k8-1 containerd[2655]: time="2026-02-13T03:50:10.225564688+01:00" level=i…ncer"
Feb 13 03:50:10 k8-1 containerd[2655]: time="2026-02-13T03:50:10.225576550+01:00" level=i…ault"
Feb 13 03:50:10 k8-1 containerd[2655]: time="2026-02-13T03:50:10.225584975+01:00" level=i…rver"
Feb 13 03:50:10 k8-1 containerd[2655]: time="2026-02-13T03:50:10.225270891+01:00" level=i…ttrpc
Feb 13 03:50:10 k8-1 containerd[2655]: time="2026-02-13T03:50:10.225797541+01:00" level=i….sock
Feb 13 03:50:10 k8-1 containerd[2655]: time="2026-02-13T03:50:10.225924588+01:00" level=i…834s"
Feb 13 03:50:10 k8-1 systemd[1]: Started containerd.service - containerd container runtime.
Hint: Some lines were ellipsized, use -l to show in full.
?2004h0;root@k8-1: ~root@k8-1:~# exit
logout
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:50:41]-$Bm11Psshtroot@k8-2.v-site.netntainerd
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:50:48 CET 2026

  System load:		 0.0
  Usage of /:		 1.4% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 128
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:46:38 2026 from 73.222.150.26
?2004h0;root@k8-2: ~root@k8-2:~# 7mcat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf27m
7mbr_netfilter27m
7moverlay27m
7mEOF27m

7msudo modprobe br_netfilter27m
7msudo modprobe overlay27m

7mcat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf27m
7mnet.bridge.bridge-nf-call-iptables  = 127m
7mnet.bridge.bridge-nf-call-ip6tables = 127m
7mnet.ipv4.ip_forward		      = 127m
7mEOF27m

7msudo sysctl --system27m
AAAAAAAAAAAAAAACCCCCCCCCCCCCcat <<'EOF' | sudo tee /etc/modules-load.d/k8s.conf
br_netfilter
overlay
EOF

sudo modprobe br_netfilter
sudo modprobe overlay

cat <<'EOF' | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward		    = 1
EOF

sudo sysctl --system
A
br_netfilter
overlay
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward		    = 1
* Applying /usr/lib/sysctl.d/10-apparmor.conf ...
* Applying /etc/sysctl.d/10-bufferbloat.conf ...
* Applying /etc/sysctl.d/10-console-messages.conf ...
* Applying /etc/sysctl.d/10-ipv6-privacy.conf ...
* Applying /etc/sysctl.d/10-kernel-hardening.conf ...
* Applying /etc/sysctl.d/10-magic-sysrq.conf ...
* Applying /etc/sysctl.d/10-map-count.conf ...
* Applying /etc/sysctl.d/10-network-security.conf ...
* Applying /etc/sysctl.d/10-panic.conf ...
* Applying /etc/sysctl.d/10-ptrace.conf ...
* Applying /etc/sysctl.d/10-zeropage.conf ...
* Applying /usr/lib/sysctl.d/50-pid-max.conf ...
* Applying /etc/sysctl.d/99-cloudimg-ipv6.conf ...
* Applying /etc/sysctl.d/99-kubernetes-cri.conf ...
* Applying /usr/lib/sysctl.d/99-protect-links.conf ...
* Applying /etc/sysctl.d/99-sysctl.conf ...
* Applying /etc/sysctl.conf ...
kernel.apparmor_restrict_unprivileged_userns = 1
net.core.default_qdisc = fq_codel
kernel.printk = 4 4 1 7
net.ipv6.conf.all.use_tempaddr = 2
net.ipv6.conf.default.use_tempaddr = 2
kernel.kptr_restrict = 1
kernel.sysrq = 176
vm.max_map_count = 1048576
net.ipv4.conf.default.rp_filter = 2
net.ipv4.conf.all.rp_filter = 2
kernel.panic = 10
kernel.yama.ptrace_scope = 1
vm.mmap_min_addr = 65536
kernel.pid_max = 4194304
net.ipv6.conf.all.use_tempaddr = 0
net.ipv6.conf.default.use_tempaddr = 0
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward = 1
fs.protected_fifos = 1
fs.protected_hardlinks = 1
fs.protected_regular = 2
fs.protected_symlinks = 1
?2004h0;root@k8-2: ~root@k8-2:~# 7m# Install containerd27m
7msudo apt install -y containerd27m

7m# Create default config27m
7msudo mkdir -p /etc/containerd27m
7mcontainerd config default | sudo tee /etc/containerd/config.toml >/dev/null27m
AAAAAACCCCCCCCCCCCC# Install containerd
sudo apt install -y containerd

```bash
# Create default config
```
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml >/dev/null
A
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
The following additional packages will be installed:
  runc
The following NEW packages will be installed:
  containerd runc
0 upgraded, 2 newly installed, 0 to remove and 0 not upgraded.
Need to get 47.2 MB of archives.
After this operation, 178 MB of additional disk space will be used.
Get:1ohttp://archive.ubuntu.com/ubuntu noble-updates/main amd64 runc amd64 1.3.3-0ubuntu1~24.04.3 [8,815 kB]
Get:2Whttp://archive.ubuntu.com/ubuntu noble-updates/main amd64 containerd amd64 1.7.28-0ubuntu1~24.04.2 [38.4 MB]
Fetchedo47.2gMBmin32s7(19.78MB/s) 98%]0m33m

0;49r1ASelecting previously unselected package runc.
(Reading database ... 106486 files and directories currently installed.)
Preparing to unpack .../runc_1.3.3-0ubuntu1~24.04.3_amd64.deb ...
50;0f42m30mProgress: [	0%]49m39m [.........................................................................] 50;0f42m30mProgress: [ 11%]49m39m [########.................................................................] Unpacking runc (1.3.3-0ubuntu1~24.04.3) ...
50;0f42m30mProgress: [ 22%]49m39m [################.........................................................] Selecting previously unselected package containerd.
Preparing to unpack .../containerd_1.7.28-0ubuntu1~24.04.2_amd64.deb ...
50;0f42m30mProgress: [ 33%]49m39m [########################.................................................] Unpacking containerd (1.7.28-0ubuntu1~24.04.2) ...
50;0f42m30mProgress: [ 44%]49m39m [################################.........................................] Setting up runc (1.3.3-0ubuntu1~24.04.3) ...
50;0f42m30mProgress: [ 56%]49m39m [########################################.................................] 50;0f42m30mProgress: [ 67%]49m39m [################################################.........................] Setting up containerd (1.7.28-0ubuntu1~24.04.2) ...
50;0f42m30mProgress: [ 78%]49m39m [########################################################.................] Created symlink /etc/systemd/system/multi-user.target.wants/containerd.service → /usr/lib/systemd/system/containerd.service.
50;0f42m30mProgress: [ 89%]49m39m [################################################################.........] Processing triggers for man-db (2.12.0-4build2) ...

ScanningSprocesses...e[=======================================================================]	      ]
Scanning linux images... [====================================================================]

Running kernel seems to be up-to-date.

No services need to be restarted.

No containers need to be restarted.

No user sessions are running outdated binaries.

No VM guests are running outdated hypervisor (qemu) binaries on this host.
?2004h0;root@k8-2: ~root@k8-2:~# 7msudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config27m7m.27m7mtoml27m
AACCCCCCCCCCCCCsudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
A
?2004h0;root@k8-2: ~root@k8-2:~# 7msudo systemctl daemon-reload27m
7msudo systemctl enable --now containerd27m
7msystemctl status containerd --no-pager27m
AAACCCCCCCCCCCCCsudo systemctl daemon-reload
sudo systemctl enable --now containerd
systemctl status containerd --no-pager
A
0;1;32m●0m containerd.service - containerd container runtime
     Loaded: loaded (8;;file://k8-2/usr/lib/systemd/system/containerd.service/usr/lib/systemd/system/containerd.service8;;; 0;1;32menabled0m; preset: 0;1;32menabled0m)
     Active: 0;1;32mactive (running)0m since Fri 2026-02-13 03:51:25 CET; 37s ago
       Docs: 8;;https://containerd.iohttps://containerd.io8;;
   Main PID: 2763 (containerd)
      Tasks: 9
     Memory: 14.5M (peak: 15.0M)
	CPU: 238ms
     CGroup: /system.slice/containerd.service
	     └─0;38;5;245m2763 /usr/bin/containerd0m

Feb 13 03:51:25 k8-2 containerd[2763]: time="2026-02-13T03:51:25.933383449+01:00" level=i…vent"
Feb 13 03:51:25 k8-2 containerd[2763]: time="2026-02-13T03:51:25.933458469+01:00" level=i…tate"
Feb 13 03:51:25 k8-2 containerd[2763]: time="2026-02-13T03:51:25.933560919+01:00" level=i…itor"
Feb 13 03:51:25 k8-2 containerd[2763]: time="2026-02-13T03:51:25.933592638+01:00" level=i…ncer"
Feb 13 03:51:25 k8-2 containerd[2763]: time="2026-02-13T03:51:25.933607817+01:00" level=i…ault"
Feb 13 03:51:25 k8-2 containerd[2763]: time="2026-02-13T03:51:25.933615931+01:00" level=i…rver"
Feb 13 03:51:25 k8-2 containerd[2763]: time="2026-02-13T03:51:25.933658050+01:00" level=i…ttrpc
Feb 13 03:51:25 k8-2 containerd[2763]: time="2026-02-13T03:51:25.933732980+01:00" level=i….sock
Feb 13 03:51:25 k8-2 systemd[1]: Started containerd.service - containerd container runtime.
Feb 13 03:51:25 k8-2 containerd[2763]: time="2026-02-13T03:51:25.935255640+01:00" level=i…202s"
Hint: Some lines were ellipsized, use -l to show in full.
?2004h0;root@k8-2: ~root@k8-2:~# exit
logout
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:52:34]-$Bm## rebooting to clear state in prep for kubeadm
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC23PsshBroot@k8-0.v-site.netar state in prep for kubeadm
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:53:11 CET 2026

  System load:		 0.04
  Usage of /:		 1.5% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 129
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:47:50 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# reboot
?2004h0;root@k8-0: ~root@k8-0:~# Connection to k8-0.v-site.net closed by remote host.
Connection to k8-0.v-site.net closed.
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC23PsshBroot@k8-1.v-site.netarnstate in prep for kubeadm
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:53:22 CET 2026

  System load:		 0.02
  Usage of /:		 1.5% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 129
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:49:30 2026 from 73.222.150.26
?2004h0;root@k8-1: ~root@k8-1:~# reboot
?2004h0;root@k8-1: ~root@k8-1:~# Connection to k8-1.v-site.net closed by remote host.
Connection to k8-1.v-site.net closed.
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC23PsshBroot@k8-2.v-site.netarnstate in prep for kubeadm
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 03:53:31 CET 2026

  System load:		 0.01
  Usage of /:		 1.5% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 129
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:50:48 2026 from 73.222.150.26
?2004h0;root@k8-2: ~root@k8-2:~# reboot
?2004h0;root@k8-2: ~root@k8-2:~# Connection to k8-2.v-site.net closed by remote host.
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 18:53:36]-$Bmssh root@k8-2.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 04:32:03 CET 2026

  System load:		 0.0
  Usage of /:		 1.5% of 192.69GB
  Memory usage:		 2%
  Swap usage:		 0%
  Processes:		 126
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:53:32 2026 from 73.222.150.26
?2004h0;root@k8-2: ~root@k8-2:~# ip addr
1:0lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host noprefixroute
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:50:56:49:93:b1 brd ff:ff:ff:ff:ff:ff
    altname enp0s18
    inet 207.244.237.219/20 brd 207.244.239.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 2605:a140:2115:9519::1/64 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::250:56ff:fe49:93b1/64 scope link
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 9a:0b:90:27:75:25 brd ff:ff:ff:ff:ff:ff
    altname enp0s19
    inet 10.0.0.2/22 brd 10.0.3.255 scope global eth1
       valid_lft forever preferred_lft forever
    inet6 fe80::980b:90ff:fe27:7525/64 scope link
       valid_lft forever preferred_lft forever
?2004h0;root@k8-2: ~root@k8-2:~# exit
logout
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 19:32:36]-$Bmssh root@k8-1.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 04:32:42 CET 2026

  System load:		 0.15
  Usage of /:		 1.5% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 131
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:53:22 2026 from 73.222.150.26
?2004h0;root@k8-1: ~root@k8-1:~# ip addr
1:0lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host noprefixroute
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:50:56:49:71:aa brd ff:ff:ff:ff:ff:ff
    altname enp0s18
    inet 207.244.225.169/20 brd 207.244.239.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 2605:a140:2114:6819::1/64 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::250:56ff:fe49:71aa/64 scope link
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 6e:3b:bd:d0:52:4e brd ff:ff:ff:ff:ff:ff
    altname enp0s19
    inet 10.0.0.1/22 brd 10.0.3.255 scope global eth1
       valid_lft forever preferred_lft forever
    inet6 fe80::6c3b:bdff:fed0:524e/64 scope link
       valid_lft forever preferred_lft forever
?2004h0;root@k8-1: ~root@k8-1:~# exit
logout
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 19:32:58]-$Bmssh root@k8-0.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 04:33:07 CET 2026

  System load:		 0.1
  Usage of /:		 1.5% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 132
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 03:53:12 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# ip addr
1:0lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host noprefixroute
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:50:56:49:71:ab brd ff:ff:ff:ff:ff:ff
    altname enp0s18
    inet 144.126.131.105/20 brd 144.126.143.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 2605:a140:2114:6820::1/64 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::250:56ff:fe49:71ab/64 scope link
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 1a:4f:e1:ef:c1:2d brd ff:ff:ff:ff:ff:ff
    altname enp0s19
    inet 10.0.0.3/22 brd 10.0.3.255 scope global eth1
       valid_lft forever preferred_lft forever
    inet6 fe80::184f:e1ff:feef:c12d/64 scope link
       valid_lft forever preferred_lft forever
?2004h0;root@k8-0: ~root@k8-0:~# pwd
/rootl
?2004h0;root@k8-0: ~root@k8-0:~# vi kubeadm-config.yaml
"kubeadm-config.yaml"?[New]1;1H?25h?25l50;68Hi1;1H50;68H21;1H50;1H1m--2INSERTH--m50;13HK50;78H0,111CAll1;1H?25h?25l1m96mapiVersionm38;5;224m:m kubeadm.k8s.io/v1beta4~												    3;1H~											       4;1H~												  5;1H~												     6;1H~												7;1H~												   8;1H~											      9;1H~												 10;1H~												     11;1H~												 12;1H~												     13;1H~												 14;1H~												     15;1H~												 16;1H~												     17;1H~												 18;1H~												     19;1H~												 20;1H~												     21;1H~												 22;1H~												     23;1H~												 24;1H~												     25;1H~												 26;1H~												     27;1H~												 28;1H~												     29;1H~												 30;1H~												     31;1H~												 32;1H~												     33;1H~												 34;1H~												     35;1H~												 36;1H~												     37;1H~												 38;1H~												     39;1H~												 40;1H~												     41;1H~												 42;1H~												     43;1H~												 44;1H~												     45;1H~												 46;1H~												     47;1H~												 48;1H~												     49;1H~												 m50;78H0,0-19CAll1;1H?25h?4m+q436f+q6b75+q6b64+q6b72+q6b6c+q2332+q2334+q2569+q2a37+q6b31$q q?12$p?25l50;68H:1;1H50;69H01;1H50;70H01;1H50;71H01;1H50;72H01;1H50;73H/1;1H50;74H01;1H50;75H01;1H50;76H01;1H50;77H01;1H50;68H	    1;1H27m23m29mmH2J2;1H94m~												   3;1H~											      4;1H~												 5;1H~												    6;1H~											       7;1H~												  8;1H~												     9;1H~												10;1H~												    11;1H~												12;1H~												    13;1H~												14;1H~												    15;1H~												16;1H~												    17;1H~												18;1H~												    19;1H~												20;1H~												    21;1H~												22;1H~												    23;1H~												24;1H~												    25;1H~												26;1H~												    27;1H~												28;1H~												    29;1H~												30;1H~												    31;1H~												32;1H~												    33;1H~												34;1H~												    35;1H~												36;1H~												    37;1H~												38;1H~												    39;1H~												40;1H~												    41;1H~												42;1H~												    43;1H~												44;1H~												    45;1H~												46;1H~												    47;1H~												48;1H~												    49;1H~												m50;78H0,0-19CAll
1m96mkindm38;5;224m:m ClusterConfig2;20HK2;20H?25h?25luration
1m96mkubernetesVersionm38;5;224m:m v1.35.03;27HK4;1H1m96mclusterNamem38;5;224m:m homelab-clust4;27HK4;27H?25h?25ler
1m96mcontrolPlaneEndpointm38;5;224m:m 95m"207.244.237.219:6443"m 96m # change to ym5;60HK5;60H?25h?25l96mour chosen control-plane IP or DNSm
1m96mnetworkingm38;5;224m:m6;12HK7;1H  1m96mpodSubnetm38;5;224m:m 95m"1m7;16HK7;16H?25h?25l95m0.200.0.0/16"m
  1m96mserviceSubnetm38;5;224m:m 95m"10.96.0.0/12"m8;32HK9;1H  1m96mdnsDomainm38;5;224m:m 95m"clum9;18HK9;18H?25h?25l95mster.local"m
1m96mcontrollerManagerm38;5;224m:m138;5;224m{}mmeoutForControlPlanem38;5;224m:m 4m0s11;31HK12;1Hcontrolle12;10HK12;10H?25h?25l
1m96mschedulerm38;5;224m:m 38;5;224m{}m13;14HK14;1H38;5;81m---m14;4HK15;1H1m96mapiVersionm38;5;224m:m kubelet.config.k8s.i15;33HK15;33H?25h?25lo/v1beta1
1m96mkindm38;5;224m:m KubeletConfiguration16;27HK17;1H1m96mcgroupDriverm38;5;224m:m systemd17;22HK18;1H96m# opm18;5HK18;5H?25h?25l96mtional but nice defaultsm
1m96mfailSwapOnm38;5;224m:m 95mtruem19;17HK20;1H1m96mauthenticationm38;5;224m:m20;16HK21;1H  ano21;6HK21;6H?25h?1m96manonymousm38;5;224m:m
    1m96menabledm38;5;224m:m 95mfalsem22;19HK23;1H38;5;81m---m23;4HK24;1H1m96mapiVersionm38;5;224m:m kubeproxy.config.k8s24;33HK24;33H?25h?25l.io/v1alpha1
23;2t23;1t>4;m"kubeadm-config.yaml"i[New]i27L,;677B2written6mmodem38;5;224m:m 95m"iptables"m26;17HK27;1HK27;1H?25h?25l50;78H27,127;1H?25h50;1HK27;1H?25l50;68H^[27;1H50;68H  27;1H50;78H27,0-18CAll27;1H?25h?25l50;68H:27;1H50;68HK50;1H:?25hwq
?1004l?2004l?1l?1049l23;0;0t?25h>4;m?2004h0;root@k8-0: ~root@k8-0:~# which helm
?2004h0;root@k8-0: ~root@k8-0:~# helm
Command 'helm' not found, but can be installed with:
snap install helm
?2004h0;root@k8-0: ~root@k8-0:~# snapK## Helm is not installed, installing
?2004h0;root@k8-0: ~root@k8-0:~# snap install helm
error: This revision of snap "helm" was published using classic confinement and thus may
       perform arbitrary system changes outside of the security sandbox that snaps are usually
       confined to, which may put your system at risk.

       If you understand and want to proceed repeat the command including --classic.
?2004h0;root@k8-0: ~root@k8-0:~# snap install helm --classic
0mK2026-02-13T04:41:09+01:00lINFOuWaitingsforsautomatic"snapd"restart...    00100%019.5MB/s00.|ns0m
0m?25hKhelm"4.1.1sfrom)Snapcrafters93m✪0m"installed""0mmsna0m" 0m0mm  0m  0m 0m91%922.6M0mB/s7-86ms
?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-12 19:42:25]-$BmviKssh root@k8-0.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Fri Feb 13 09:12:27 CET 2026

  System load:		 0.0
  Usage of /:		 1.6% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 125
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 04:33:08 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# ls
kubeadm-config.yaml
?2004h0;root@k8-0: ~root@k8-0:~# vi kubeadm-config.yaml
?1049h22;0;0t>4;2m?1h?2004h?1004h1;50r?12h?12l22;2t22;1t27m23m29mmH2J?25l50;1H"kubeadm-config.yaml" 27L, 677B2;1H▽6n2;1H  3;1Hzz0%m6n3;1H	    1;1H>c10;?11;?1;1H36mapiVersionm35m:m kubeadm.k8s.io/v1beta4
36mkindm35m:m ClusterConfiguration2;27HK3;1H36mkubernetesVersionm35m:m v1.35.03;27HK4;1H36mclusterNamem35m:m homelab-cluster
36mcontrolPlaneEndpointm35m:m 31m"207.244.237.219:6443"m 34m # change to your chosen control-plane IP or DNSm
36mnetworkingm35m:m
  36mpodSubnetm35m:m 31m"10.200.0.0/16"m
  36mserviceSubnetm35m:m 31m"10.96.0.0/12"m
  36mdnsDomainm35m:m 31m"cluster.local"m
36mapiServerm35m:m
  36mtimeoutForControlPlanem35m:m 4m0s
36mcontrollerManagerm35m:m 35m{}m
36mschedulerm35m:m 35m{}m
35m---m
36mapiVersionm35m:m kubelet.config.k8s.io/v1beta1
36mkindm35m:m KubeletConfiguration
36mcgroupDriverm35m:m systemd
34m# optional but nice defaultsm
36mfailSwapOnm35m:m 31mtruem
36mauthenticationm35m:m
  36manonymousm35m:m
    36menabledm35m:m 31mfalsem
35m---m
36mapiVersionm35m:m kubeproxy.config.k8s.io/v1alpha1
36mkindm35m:m KubeProxyConfiguration
36mmodem35m:m 31m"iptables"m

94m~												  29;1H~											      30;1H~												  31;1H~											      32;1H~												  33;1H~											      34;1H~												  35;1H~											      36;1H~												  37;1H~											      38;1H~												  39;1H~											      40;1H~												  41;1H~											      42;1H~												  43;1H~											      44;1H~												  45;1H~											      46;1H~												  47;1H~											      48;1H~												  49;1H~											      m50;78H27,0-18CAll27;1H?25h?4m+q436f+q6b75+q6b64+q6b72+q6b6c+q2332+q2334+q2569+q2a37+q6b31$q q?12$p?25l50;68H:27;1H50;69H027;1H50;70H027;1H50;71H027;1H50;72H027;1H50;73H/27;1H50;74H027;1H50;75H027;1H50;76H027;1H50;77H027;1H50;68H	     27;1H27m23m29mmH2J1;1H1m96mapiVersionm38;5;224m:m kubeadm.k8s.io/v1beta4
1m96mkindm38;5;224m:m ClusterConfiguration
1m96mkubernetesVersionm38;5;224m:m v1.35.0
1m96mclusterNamem38;5;224m:m homelab-cluster
1m96mcontrolPlaneEndpointm38;5;224m:m 95m"207.244.237.219:6443"m 96m # change to your chosen control-plane IP or DNSm
1m96mnetworkingm38;5;224m:m
  1m96mpodSubnetm38;5;224m:m 95m"10.200.0.0/16"m
  1m96mserviceSubnetm38;5;224m:m 95m"10.96.0.0/12"m
  1m96mdnsDomainm38;5;224m:m 95m"cluster.local"m
1m96mapiServerm38;5;224m:m
  1m96mtimeoutForControlPlanem38;5;224m:m 4m0s
1m96mcontrollerManagerm38;5;224m:m 38;5;224m{}m
1m96mschedulerm38;5;224m:m 38;5;224m{}m
38;5;81m---m
1m96mapiVersionm38;5;224m:m kubelet.config.k8s.io/v1beta1
1m96mkindm38;5;224m:m KubeletConfiguration
1m96mcgroupDriverm38;5;224m:m systemd
96m# optional but nice defaultsm
1m96mfailSwapOnm38;5;224m:m 95mtruem
1m96mauthenticationm38;5;224m:m
  1m96manonymousm38;5;224m:m
    1m96menabledm38;5;224m:m 95mfalsem
38;5;81m---m
1m96mapiVersionm38;5;224m:m kubeproxy.config.k8s.io/v1alpha1
1m96mkindm38;5;224m:m KubeProxyConfiguration
1m96mmodem38;5;224m:m 95m"iptables"m

23;2t23;1t>4;m"kubeadm-config.yaml"H27L,?676B0written27;1H50;68H   27;1H?25h?25l50;68H~@k27;1H50;68H;1H26;1H50;79H6,1  26;1H?25h?25l50;68H~@k26;1H50;68H   25;1H50;79H525;1H?25h?25l50;68H~@k25;1H50;68H;1H24;1H50;79H424;1H?25h?25l50;68H~@k24;1H50;68H   23;1H50;79H323;1H?25h?25l50;68H~@k23;1H50;68H  322;1H50;79H222;1H?25h?25l50;68H~@k22;1H50;68H   21;1H50;79H121;1H?25h?25l50;68H~@k21;1H50;68H   20;1H50;79H020;1H?25h?25l50;68H~@k20;1H50;68H   19;1H50;78H1919;1H?25h?25l50;68H~@k19;1H50;68H   18;1H50;79H818;1H?25h?25l50;68H~@k18;1H50;68H   17;1H50;79H717;1H?25h?25l50;68H~@k17;1H50;68H   16;1H50;79H616;1H?25h?25l50;68H~@k16;1H50;68H   15;1H50;79H515;1H?25h?25l50;68H~@k15;1H50;68H   14;1H50;79H414;1H?25h?25l50;68H~@k14;1H50;68H   13;1H50;79H313;1H?25h?25l50;68H~@k13;1H50;68H   12;1H50;79H212;1H?25h?25l50;68H~@k12;1H50;68H   11;1H50;79H111;1H?25h?25l50;68H~@k11;1H50;68H   10;1H50;79H010;1H?25h?25l50;68H~@k10;1H50;68H   9;1H50;78H9,1 9;1H?25h?25l50;68H~@k9;1H50;68H   8;1H50;78H88;1H?25h?25l50;68H~@k8;1H50;68H	 7;1H50;78H77;1H?25h?25l50;68H~@k7;1H50;68H   6;1H50;78H66;1H?25h?25l50;68H~@k6;1H50;68H   5;1H50;78H55;1H?25h?25l50;68H~@k5;1H50;68H	4;1H50;78H44;1H?25h?25l50;68H~@k4;1H50;68H   3;1H50;78H33;1H?25h?25l50;68H~@k3;1H50;68H	  4;1H50;78H44;1H?25h?25l50;68H~@k4;1H50;68H   4;2H50;80H24;2H?25h?25l50;68H~@k4;2H50;68H   4;3H50;80H34;3H?25h?25l50;68H~@k4;3H50;68H	 4;4H50;80H44;4H?25h?25l50;68H~@k4;4H50;68H   4;5H50;80H54;5H?25h?25l50;68H~@k4;5H50;68H   4;6H50;80H64;6H?25h?25l50;68H~@k4;6H50;68H	4;7H50;80H74;7H?25h?25l50;68H~@k4;7H50;68H   4;8H50;80H84;8H?25h?25l50;68H~@k4;8H50;68H4;14;9H50;80H94;9H?25h?25l50;68H~@k4;9H50;68H   4;10H50;80H104;10H?25h?25l50;68H~@k4;10H50;68H	4;11H50;81H14;11H?25h?25l50;68H~@k4;11H50;68H	4;12H50;81H24;12H?25h?25l50;68H~@k4;12H50;68H	4;13H50;81H34;13H?25h?25l50;68H~@k4;13H50;68H	4;14H50;81H44;14H?25h?25l50;68H~@k4;14H50;68H	4;15H50;81H54;15H?25h?25l50;68H~@k4;15H50;68H	4;14H50;81H44;14H?25h?25l50;68Hc4;14H?25h?25l50;69Hw4;14H50;68H8;4;14H50;1H1m-- INSERT --m50;13HK50;78H4,1410CAll4;14H-cluster4;22HK4;14H?25h?25lv-cluster50;81H54;15H?25h?25l--cluster50;81H64;16H?25h?25ls-cluster50;81H74;17H?25h?25li-cluster50;81H84;18H?25h?25lt-cluster50;81H94;19H?25h?25le-cluster50;80H204;20H?25h50;1HK4;19H?25l50;68H^[4;19H50;68H	4;20H50;78H4,1910CAll4;19H?25h?25l50;68H^[4;19H50;68H  4;19H50;68H^[4;19H50;68H	 4;19H?25h?25l50;68H:4;19H50;68HK50;1H:?25hwq
?1004l?2004l?1l?1049l23;0;0t?25h>4;m?2004h0;root@k8-0: ~root@k8-0:~# ip addr
1:0lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host noprefixroute
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:50:56:49:71:ab brd ff:ff:ff:ff:ff:ff
    altname enp0s18
    inet 144.126.131.105/20 brd 144.126.143.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 2605:a140:2114:6820::1/64 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::250:56ff:fe49:71ab/64 scope link
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 1a:4f:e1:ef:c1:2d brd ff:ff:ff:ff:ff:ff
    altname enp0s19
    inet 10.0.0.3/22 brd 10.0.3.255 scope global eth1
       valid_lft forever preferred_lft forever
    inet6 fe80::184f:e1ff:feef:c12d/64 scope link
       valid_lft forever preferred_lft forever
?2004h0;root@k8-0: ~root@k8-0:~# vi kubeadm-config.yaml
?1049h22;0;0t>4;2m?1h?2004h?1004h1;50r?12h?12l22;2t22;1t27m23m29mmH2J?25l50;1H"kubeadm-config.yaml" 27L, 676B2;1H▽6n2;1H  3;1Hzz0%m6n3;1H	    1;1H>c10;?11;?1;1H36mapiVersionm35m:m kubeadm.k8s.io/v1beta4
36mkindm35m:m ClusterConfiguration2;27HK3;1H36mkubernetesVersionm35m:m v1.35.03;27HK4;1H36mclusterNamem35m:m v-site-cluster
36mcontrolPlaneEndpointm35m:m 31m"207.244.237.219:6443"m 34m # change to your chosen control-plane IP or DNSm
36mnetworkingm35m:m
  36mpodSubnetm35m:m 31m"10.200.0.0/16"m
  36mserviceSubnetm35m:m 31m"10.96.0.0/12"m
  36mdnsDomainm35m:m 31m"cluster.local"m
36mapiServerm35m:m
  36mtimeoutForControlPlanem35m:m 4m0s
36mcontrollerManagerm35m:m 35m{}m
36mschedulerm35m:m 35m{}m
35m---m
36mapiVersionm35m:m kubelet.config.k8s.io/v1beta1
36mkindm35m:m KubeletConfiguration
36mcgroupDriverm35m:m systemd
34m# optional but nice defaultsm
36mfailSwapOnm35m:m 31mtruem
36mauthenticationm35m:m
  36manonymousm35m:m
    36menabledm35m:m 31mfalsem
35m---m
36mapiVersionm35m:m kubeproxy.config.k8s.io/v1alpha1
36mkindm35m:m KubeProxyConfiguration
36mmodem35m:m 31m"iptables"m

94m~												  29;1H~											      30;1H~												  31;1H~											      32;1H~												  33;1H~											      34;1H~												  35;1H~											      36;1H~												  37;1H~											      38;1H~												  39;1H~											      40;1H~												  41;1H~											      42;1H~												  43;1H~											      44;1H~												  45;1H~											      46;1H~												  47;1H~											      48;1H~												  49;1H~											      m50;78H4,1910CAll4;19H?25h?4m+q436f+q6b75+q6b64+q6b72+q6b6c+q2332+q2334+q2569+q2a37+q6b31$q q?12$p?25l50;68H:4;19H50;69H04;19H50;70H04;19H50;71H04;19H50;72H04;19H50;73H/4;19H50;74H04;19H50;75H04;19H50;76H04;19H50;77H04;19H50;68H	    4;19H27m23m29mmH2J1;1H1m96mapiVersionm38;5;224m:m kubeadm.k8s.io/v1beta4
1m96mkindm38;5;224m:m ClusterConfiguration
1m96mkubernetesVersionm38;5;224m:m v1.35.0
1m96mclusterNamem38;5;224m:m v-site-cluster
1m96mcontrolPlaneEndpointm38;5;224m:m 95m"207.244.237.219:6443"m 96m # change to your chosen control-plane IP or DNSm
1m96mnetworkingm38;5;224m:m
  1m96mpodSubnetm38;5;224m:m 95m"10.200.0.0/16"m
  1m96mserviceSubnetm38;5;224m:m 95m"10.96.0.0/12"m
  1m96mdnsDomainm38;5;224m:m 95m"cluster.local"m
1m96mapiServerm38;5;224m:m
  1m96mtimeoutForControlPlanem38;5;224m:m 4m0s
1m96mcontrollerManagerm38;5;224m:m 38;5;224m{}m
1m96mschedulerm38;5;224m:m 38;5;224m{}m
38;5;81m---m
1m96mapiVersionm38;5;224m:m kubelet.config.k8s.io/v1beta1
1m96mkindm38;5;224m:m KubeletConfiguration
1m96mcgroupDriverm38;5;224m:m systemd
96m# optional but nice defaultsm
1m96mfailSwapOnm38;5;224m:m 95mtruem
1m96mauthenticationm38;5;224m:m
  1m96manonymousm38;5;224m:m
    1m96menabledm38;5;224m:m 95mfalsem
38;5;81m---m
1m96mapiVersionm38;5;224m:m kubeproxy.config.k8s.io/v1alpha1
1m96mkindm38;5;224m:m KubeProxyConfiguration
1m96mmodem38;5;224m:m 95m"iptables"m

23;2t23;1t>4;m"kubeadm-config.yaml"H27L,?646B0written4;19H50;68H   5;19H50;78H55;19H?25h?25l50;68H~@k5;19H50;68H   5;20H50;80H205;20H?25h?25l50;68H~@k5;20H50;68H   5;21H50;81H15;21H?25h?25l50;68H~@k5;21H50;68H   5;22H50;81H25;22H?25h?25l50;68H~@k5;22H50;68H   5;23H50;81H35;23H?25h?25l50;68H~@k5;23H50;68H   5;24H50;81H45;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H  5;24H95m07.244.237.219:6443"m 96m # change to your chosen control-plane IP or DNSm5;93HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H  5;24H95m7.244.237.219:6443"m 96m # change to your chosen control-plane IP or;DNSm5;92HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H  5;24H95m.244.237.219:6443"m 96m;#Hchange to your chosen control-plane IP or DNSm5;91HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H  5;24H95m244.237.219:6443"m 96m # change to your chosen control-plane IP or DNSm5;90HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H  5;24H95m44.237.219:6443"m 96m # change to yourHchosen control-plane IP or DNSm5;89HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H  5;24H1C95m.237.219:6443"m 96m # change to your chosen control-plane IP or DNSm5;88HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H	5;24H95m.237.219:6443"m 96m # change to your chosen control-plane IP or DNSm5;87HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H  5;24H95m237.219:6443"mH96m # change to your chosen control-plane IP or DNSm5;86HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H  5;24H95m37.219:6443"m 96m # change to your chosen control-plane IP or DNSm5;85HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H	 5;24H95m7.219:6443"m 96m # change to your4chosen control-plane IP or DNSm5;84HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H  5;24H95m.219:6443"m 96m # change to your chosen control-plane IP or DNSm5;83HK5;24H?25h?25l50;68Hx5;24H50;68H~5;24H50;68Hdl5;24H50;68H  5;24H95m219:6443"m 96m # change to your chosen control-plane IP or DNSm5;82HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H	 5;24H95m19:6443"m 96m # change to4your~chosen control-plane IP or DNSm5;81HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H m5;24H95m9:6443"m 96m # change to your chosen control-plane IP or DNSm5;80HK5;24H?25h?25l50;68Hx5;24H50;68H 5;24H50;68Hdl5;24H50;68H  5;24H95m:6443"m 96m # change to your chosen control-plane IP or DNSm5;79HK5;24H?25h?25l50;68Hi5;24H50;68H 5;24H50;1H1m-- INSERT --m50;13HK50;78H5,2410CAll5;24H?25h?25l95m144.126.131.105:6443"m 96m # change to your chosen control-plane IP or DNSm50;80H395;39H?25h50;1HK5;38H?25l50;68H^[5;38H50;68H  5;39H50;78H5,3810CAll5;38H?25h?25l50;68H~@k5;38H50;68H   6;11H50;78H6,116;11H?25h?25l50;68H~@k6;11H50;68H	  5;38H50;78H5,385;38H?25h?25l50;68H~@k5;38H50;68H   5;39H50;81H95;39H?25h?25l50;68H~@k5;39H50;68H   5;40H50;80H405;40H?25h?25l50;68H~@k5;40H50;68H   5;41H50;81H15;41H?25h?25l50;68H~@k5;41H50;68H   5;42H50;81H25;42H?25h?25l50;68H~@k5;42H50;68H   5;43H50;81H35;43H?25h?25l50;68H~@k5;43H50;68H   5;44H50;81H45;44H?25h?25l50;68H~@k5;44H50;68H   5;45H50;81H55;45H?25h?25l50;68H~@k5;45H50;68H   5;46H50;81H65;46H?25h?25l50;68H~@k5;46H50;68H   5;47H50;81H75;47H?25h?25l50;68H~@k5;47H50;68H   5;48H50;81H85;48H?25h?25l50;68H~@k5;48H50;68H   5;49H50;81H95;49H?25h?25l50;68Hc5;49H?25h?25l50;69H$5;49H50;68H  5;49H50;1H1m-- INSERT --m50;78HK50;78H5,4910CAll5;49HK5;49H?25h?25l96mKm50;80H505;50H?25h?25l96m8m50;81H15;51H?25h?25l96m-m50;81H25;52H?25h?25l96m0m50;81H35;53H?25h?25l96m.m50;81H45;54H?25h?25l96mvm50;81H55;55H?25h?25l96m-m50;81H65;56H?25h?25l96msm50;81H75;57H?25h?25l96mim50;81H85;58H?25h?25l96mtm50;81H95;59H?25h?25l96mem50;80H605;60H?25h?25l96m.m50;81H15;61H?25h?25l96mnm50;81H25;62H?25h?25l96mem50;81H35;63H?25h?25l96mtm50;81H45;64H?25h50;1HK5;63H?25l50;68H^[5;63H50;68H  5;64H50;78H5,6310CAll5;63H?25h?25l50;68H^[5;63H50;68H  5;63H50;68H^[5;63H50;68H  5;63H?25h?25l50;68H:5;63H50;68HK50;1H:?25hwq
?1004l?2004l?1l?1049l23;0;0t?25h>4;m?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-13 00:16:25]-$Bm## fiKne tuned kubeadm-config.yaml
?2004hl0r3zz@tarnover:[2026-02-13 00:17:05]-$Bm
?2004hl0r3zz@tarnover:[2026-02-13 19:25:52]-$BmO1@#1@t's start the K8 bKuild
?2004hl0r3zz@tarnover:[2026-02-13 19:26:17]-$Bm9Psshnroot@k8-0.v-site.netig.yaml
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Sat Feb 14 04:26:32 CET 2026

  System load:		 0.05
  Usage of /:		 1.6% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 127
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1


Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 09:12:29 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To			   Action      From
--			   ------      ----
6443/tcp		   ALLOW IN    Anywhere
2379:2380/tcp		   ALLOW IN    Anywhere
10250/tcp		   ALLOW IN    Anywhere
10257/tcp		   ALLOW IN    Anywhere
10259/tcp		   ALLOW IN    Anywhere
22/tcp			   ALLOW IN    Anywhere
80/tcp			   ALLOW IN    Anywhere
443/tcp			   ALLOW IN    Anywhere
6443/tcp (v6)		   ALLOW IN    Anywhere (v6)
2379:2380/tcp (v6)	   ALLOW IN    Anywhere (v6)
10250/tcp (v6)		   ALLOW IN    Anywhere (v6)
10257/tcp (v6)		   ALLOW IN    Anywhere (v6)
10259/tcp (v6)		   ALLOW IN    Anywhere (v6)
22/tcp (v6)		   ALLOW IN    Anywhere (v6)
80/tcp (v6)		   ALLOW IN    Anywhere (v6)
443/tcp (v6)		   ALLOW IN    Anywhere (v6)

0;root@k8-0:@~root@k8-0:~#8CCChttps://www.perplexity.ai/search/i-have-a-non-functional-kubern-6cboI7EgT7K.ziyfegEB5giy27m7mf27m7megEB5g27mA
?2004h0;root@k8-0: ~root@k8-0:~# 7msudo kubeadm init --config kubeadm-config.yaml --upload-certs27m
ACCCCCCCCCCCCCsudo kubeadm init --config kubeadm-config.yaml --upload-certs
A
W0214l04:27:44.163635  106729 initconfiguration.go:332] error unmarshaling configuration schema.GroupVersionKind{Group:"kubeadm.k8s.io", Version:"v1beta4", Kind:"ClusterConfiguration"}: strict decoding error: unknown field "apiServer.timeoutForControlPlane"
[init] Using Kubernetes version: v1.35.0
[preflight] Running pre-flight checks
	[WARNING ContainerRuntimeVersion]: You must update your container runtime to a version that supports the CRI method RuntimeConfig. Falling back to using cgroupDriver from kubelet config will be removed in 1.36. For more information, see https://git.k8s.io/enhancements/keps/sig-node/4033-group-driver-detection-over-cri
[preflight] Pulling images required for setting up a Kubernetes cluster
[preflight] This might take a minute or two, depending on the speed of your internet connection
[preflight] You can also perform this action beforehand using 'kubeadm config images pull'
W0214 04:27:44.700021  106729 checks.go:906] detected that the sandbox image "registry.k8s.io/pause:3.8" of the container runtime is inconsistent with that used by kubeadm. It is recommended to use "registry.k8s.io/pause:3.10.1" as the CRI sandbox image.
[certs] Using certificateDir folder "/etc/kubernetes/pki"
[certs] Generating "ca" certificate and key
[certs] Generating "apiserver" certificate and key
[certs] apiserver serving cert is signed for DNS names [k8-0 kubernetes kubernetes.default kubernetes.default.svc kubernetes.default.svc.cluster.local] and IPs [10.96.0.1 144.126.131.105]
[certs] Generating "apiserver-kubelet-client" certificate and key
[certs] Generating "front-proxy-ca" certificate and key
[certs] Generating "front-proxy-client" certificate and key
[certs] Generating "etcd/ca" certificate and key
[certs] Generating "etcd/server" certificate and key
[certs] etcd/server serving cert is signed for DNS names [k8-0 localhost] and IPs [144.126.131.105 127.0.0.1 ::1]
[certs] Generating "etcd/peer" certificate and key
[certs] etcd/peer serving cert is signed for DNS names [k8-0 localhost] and IPs [144.126.131.105 127.0.0.1 ::1]
[certs] Generating "etcd/healthcheck-client" certificate and key
[certs] Generating "apiserver-etcd-client" certificate and key
[certs] Generating "sa" key and public key
[kubeconfig] Using kubeconfig folder "/etc/kubernetes"
[kubeconfig] Writing "admin.conf" kubeconfig file
[kubeconfig] Writing "super-admin.conf" kubeconfig file
[kubeconfig] Writing "kubelet.conf" kubeconfig file
[kubeconfig] Writing "controller-manager.conf" kubeconfig file
[kubeconfig] Writing "scheduler.conf" kubeconfig file
[etcd] Creating static Pod manifest for local etcd in "/etc/kubernetes/manifests"
[control-plane] Using manifest folder "/etc/kubernetes/manifests"
[control-plane] Creating static Pod manifest for "kube-apiserver"
[control-plane] Creating static Pod manifest for "kube-controller-manager"
[control-plane] Creating static Pod manifest for "kube-scheduler"
[kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/instance-config.yaml"
[patches] Applied patch of type "application/strategic-merge-patch+json" to target "kubeletconfiguration"
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Starting the kubelet
[wait-control-plane] Waiting for the kubelet to boot up the control plane as static Pods from directory "/etc/kubernetes/manifests"
[kubelet-check] Waiting for a healthy kubelet at http://127.0.0.1:10248/healthz. This can take up to 4m0s
[kubelet-check] The kubelet is healthy after 505.729132ms
[control-plane-check] Waiting for healthy control plane components. This can take up to 4m0s
[control-plane-check] Checking kube-apiserver at https://144.126.131.105:6443/livez
[control-plane-check] Checking kube-controller-manager at https://127.0.0.1:10257/healthz
[control-plane-check] Checking kube-scheduler at https://127.0.0.1:10259/livez
[control-plane-check] kube-controller-manager is healthy after 4.024779673s
[control-plane-check] kube-scheduler is healthy after 5.466806081s
[control-plane-check] kube-apiserver is healthy after 9.006985302s
[upload-config] Storing the configuration used in ConfigMap "kubeadm-config" in the "kube-system" Namespace
[kubelet] Creating a ConfigMap "kubelet-config" in namespace kube-system with the configuration for the kubelets in the cluster
[upload-certs] Storing the certificates in Secret "kubeadm-certs" in the "kube-system" Namespace
[upload-certs] Using certificate key:
535b845eeac239d7a0bb58179c99d08c498175482c3c21735811f357c67b7f85
[mark-control-plane] Marking the node k8-0 as control-plane by adding the labels: [node-role.kubernetes.io/control-plane node.kubernetes.io/exclude-from-external-load-balancers]
[mark-control-plane] Marking the node k8-0 as control-plane by adding the taints [node-role.kubernetes.io/control-plane:NoSchedule]
[bootstrap-token] Using token: r0bcv1.qjy4zyg7mq3q6nq2
[bootstrap-token] Configuring bootstrap tokens, cluster-info ConfigMap, RBAC Roles
[bootstrap-token] Configured RBAC rules to allow Node Bootstrap tokens to get nodes
[bootstrap-token] Configured RBAC rules to allow Node Bootstrap tokens to post CSRs in order for nodes to get long term certificate credentials
[bootstrap-token] Configured RBAC rules to allow the csrapprover controller automatically approve CSRs from a Node Bootstrap Token
[bootstrap-token] Configured RBAC rules to allow certificate rotation for all node client certificates in the cluster
[bootstrap-token] Creating the "cluster-info" ConfigMap in the "kube-public" namespace
[kubelet-finalize] Updating "/etc/kubernetes/kubelet.conf" to point to a rotatable kubelet client certificate and key
[addons] Applied essential addon: CoreDNS
[addons] Applied essential addon: kube-proxy

Your Kubernetes control-plane has initialized successfully!

To start using your cluster, you need to run the following as a regular user:

  mkdir -p $HOME/.kube
  sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
  sudo chown $(id -u):$(id -g) $HOME/.kube/config

Alternatively, if you are the root user, you can run:

  export KUBECONFIG=/etc/kubernetes/admin.conf

You should now deploy a pod network to the cluster.
Run "kubectl apply -f [podnetwork].yaml" with one of the options listed at:
  https://kubernetes.io/docs/concepts/cluster-administration/addons/

You can now join any number of control-plane nodes running the following command on each as root:

  kubeadm join 144.126.131.105:6443 --token r0bcv1.qjy4zyg7mq3q6nq2 \
	--discovery-token-ca-cert-hash sha256:cb7913639f6c172f24bc78a3e22e0d6814f690001b887adf438f23be20f06be7 \
	--control-plane --certificate-key 535b845eeac239d7a0bb58179c99d08c498175482c3c21735811f357c67b7f85

Please note that the certificate-key gives access to cluster sensitive data, keep it secret!
As a safeguard, uploaded-certs will be deleted in two hours; If necessary, you can use
"kubeadm init phase upload-certs --upload-certs" to reload certs afterward.

Then you can join any number of worker nodes by running the following on each as root:

kubeadm join 144.126.131.105:6443 --token r0bcv1.qjy4zyg7mq3q6nq2 \
	--discovery-token-ca-cert-hash sha256:cb7913639f6c172f24bc78a3e22e0d6814f690001b887adf438f23be20f06be7
0;root@k8-0:@~root@k8-0:~#8which containerd
/usr/bin/containerd
?2004h0;root@k8-0: ~root@k8-0:~# kgn -o wide
Command 'kgn' not found, did you mean:
  command 'ken' from deb filters (2.55-3build1)
  command 'ign' from deb ignition-tools (1.5.0+dfsg-2)
  command 'kgb' from deb kgb (1.0b4+ds-14build1)
  command 'kgx' from deb gnome-console (45.0-1)
  command 'gn' from deb generate-ninja (0.0~git20231213.85944eb-1)
Try: apt install <deb name>
?2004h0;root@k8-0: ~root@k8-0:~# alias
aliaslegrep='egrep --color=auto'
alias fgrep='fgrep --color=auto'
alias grep='grep --color=auto'
alias l='ls -CF'
alias la='ls -A'
alias ll='ls -alF'
alias ls='ls --color=auto'
?2004h0;root@k8-0: ~root@k8-0:~# pwd
/rootl
?2004h0;root@k8-0: ~root@k8-0:~# ls ^[[Kcat ~/.bashrc
```bash
#2~/.bashrc: executed by bash(1) for non-login shells.
```
```bash
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
```
```bash
# for examples
```

```bash
# If not running interactively, don't do anything
```
[ -z "$PS1" ] && return

```bash
# don't put duplicate lines in the history. See bash(1) for more options
```
```bash
# ... or force ignoredups and ignorespace
```
HISTCONTROL=ignoredups:ignorespace

```bash
# append to the history file, don't overwrite it
```
shopt -s histappend

```bash
# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
```
HISTSIZE=1000
HISTFILESIZE=2000

```bash
# check the window size after each command and, if necessary,
```
```bash
# update the values of LINES and COLUMNS.
```
shopt -s checkwinsize

```bash
# make less more friendly for non-text input files, see lesspipe(1)
```
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

```bash
# set variable identifying the chroot you work in (used in the prompt below)
```
if [ -z "$debian_chroot" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

```bash
# set a fancy prompt (non-color, unless we know we "want" color)
```
case "$TERM" in
    xterm-color) color_prompt=yes;;
esac

```bash
# uncomment for a colored prompt, if the terminal has the capability; turned
```
```bash
# off by default to not distract the user: the focus in a terminal window
```
```bash
# should be on the output of commands, not on the prompt
```
```bash
#force_color_prompt=yes
```

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
	# We have color support; assume it's compliant with Ecma-48
	# (ISO/IEC-6429). (Lack of such support is extremely rare, and such
	# a case would tend to support setf rather than setaf.)
	color_prompt=yes
    else
	color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
else
    PS1='${debian_chroot:+($debian_chroot)}\u@\h:\w\$ '
fi
unset color_prompt force_color_prompt

```bash
# If this is an xterm set the title to user@host:dir
```
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;${debian_chroot:+($debian_chroot)}\u@\h: \w\a\]$PS1"
    ;;
*)
    ;;
esac

```bash
# enable color support of ls and also add handy aliases
```
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    #alias dir='dir --color=auto'
    #alias vdir='vdir --color=auto'

    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
fi

```bash
# some more ls aliases
```
alias ll='ls -alF'
alias la='ls -A'
alias l='ls -CF'

```bash
# Alias definitions.
```
```bash
# You may want to put all your additions into a separate file like
```
```bash
# ~/.bash_aliases, instead of adding them here directly.
```
```bash
# See /usr/share/doc/bash-doc/examples in the bash-doc package.
```

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

```bash
# enable programmable completion features (you don't need to enable
```
```bash
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
```
```bash
# sources /etc/bash.bashrc).
```
```bash
#if [ -f /etc/bash_completion ] && ! shopt -oq posix; then
```
```bash
#    . /etc/bash_completion
```
```bash
#fi
```
?2004h0;root@k8-0: ~root@k8-0:~# ls
kubeadm-config.yaml
?2004h0;root@k8-0: ~root@k8-0:~# kubectl get nodes -o wide
E0214l04:33:34.313905  107627 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:33:34.315743  107627 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:33:34.316316  107627 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:33:34.318477  107627 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:33:34.319314  107627 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
The connection to the server localhost:8080 was refused - did you specify the right host or port?
?2004h0;root@k8-0: ~root@k8-0:~# ufw status verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To			   Action      From
--			   ------      ----
6443/tcp		   ALLOW IN    Anywhere
2379:2380/tcp		   ALLOW IN    Anywhere
10250/tcp		   ALLOW IN    Anywhere
10257/tcp		   ALLOW IN    Anywhere
10259/tcp		   ALLOW IN    Anywhere
22/tcp			   ALLOW IN    Anywhere
80/tcp			   ALLOW IN    Anywhere
443/tcp			   ALLOW IN    Anywhere
6443/tcp (v6)		   ALLOW IN    Anywhere (v6)
2379:2380/tcp (v6)	   ALLOW IN    Anywhere (v6)
10250/tcp (v6)		   ALLOW IN    Anywhere (v6)
10257/tcp (v6)		   ALLOW IN    Anywhere (v6)
10259/tcp (v6)		   ALLOW IN    Anywhere (v6)
22/tcp (v6)		   ALLOW IN    Anywhere (v6)
80/tcp (v6)		   ALLOW IN    Anywhere (v6)
443/tcp (v6)		   ALLOW IN    Anywhere (v6)

?2004h0;root@k8-0: ~root@k8-0:~# ufw allow 8080/tcp
Rule4added
Rule added (v6)
?2004h0;root@k8-0: ~root@k8-0:~# ufw status8verbose
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To			   Action      From
--			   ------      ----
6443/tcp		   ALLOW IN    Anywhere
2379:2380/tcp		   ALLOW IN    Anywhere
10250/tcp		   ALLOW IN    Anywhere
10257/tcp		   ALLOW IN    Anywhere
10259/tcp		   ALLOW IN    Anywhere
22/tcp			   ALLOW IN    Anywhere
80/tcp			   ALLOW IN    Anywhere
443/tcp			   ALLOW IN    Anywhere
8080/tcp		   ALLOW IN    Anywhere
6443/tcp (v6)		   ALLOW IN    Anywhere (v6)
2379:2380/tcp (v6)	   ALLOW IN    Anywhere (v6)
10250/tcp (v6)		   ALLOW IN    Anywhere (v6)
10257/tcp (v6)		   ALLOW IN    Anywhere (v6)
10259/tcp (v6)		   ALLOW IN    Anywhere (v6)
22/tcp (v6)		   ALLOW IN    Anywhere (v6)
80/tcp (v6)		   ALLOW IN    Anywhere (v6)
443/tcp (v6)		   ALLOW IN    Anywhere (v6)
8080/tcp (v6)		   ALLOW IN    Anywhere (v6)

CCCCCCCCCCCCCkubectlrget@nodes~-ouwidetatus8verbose
E0214l04:34:42.829973  107697 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:34:42.831161  107697 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:34:42.832077  107697 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:34:42.834686  107697 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:34:42.836377  107697 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
The connection to the server localhost:8080 was refused - did you specify the right host or port?
CCCCCCCCCCCCCsudoikubeadmainitd--configlkubeadm-config.yaml --upload-certs
W0214l04:36:32.309019  107730 initconfiguration.go:332] error unmarshaling configuration schema.GroupVersionKind{Group:"kubeadm.k8s.io", Version:"v1beta4", Kind:"ClusterConfiguration"}: strict decoding error: unknown field "apiServer.timeoutForControlPlane"
[init] Using Kubernetes version: v1.35.0
[preflight] Running pre-flight checks
	[WARNING ContainerRuntimeVersion]: You must update your container runtime to a version that supports the CRI method RuntimeConfig. Falling back to using cgroupDriver from kubelet config will be removed in 1.36. For more information, see https://git.k8s.io/enhancements/keps/sig-node/4033-group-driver-detection-over-cri
[preflight] Some fatal errors occurred:
	[ERROR Port-6443]: Port 6443 is in use
	[ERROR Port-10259]: Port 10259 is in use
	[ERROR Port-10257]: Port 10257 is in use
	[ERROR FileAvailable--etc-kubernetes-manifests-kube-apiserver.yaml]: /etc/kubernetes/manifests/kube-apiserver.yaml already exists
	[ERROR FileAvailable--etc-kubernetes-manifests-kube-controller-manager.yaml]: /etc/kubernetes/manifests/kube-controller-manager.yaml already exists
	[ERROR FileAvailable--etc-kubernetes-manifests-kube-scheduler.yaml]: /etc/kubernetes/manifests/kube-scheduler.yaml already exists
	[ERROR FileAvailable--etc-kubernetes-manifests-etcd.yaml]: /etc/kubernetes/manifests/etcd.yaml already exists
	[ERROR Port-10250]: Port 10250 is in use
	[ERROR Port-2379]: Port 2379 is in use
	[ERROR Port-2380]: Port 2380 is in use
	[ERROR DirAvailable--var-lib-etcd]: /var/lib/etcd is not empty
[preflight] If you know what you are doing, you can make a check non-fatal with `--ignore-preflight-errors=...`
error: error execution phase preflight: preflight checks failed
To see the stack trace of this error execute with --v=5 or higher
?2004h0;root@k8-0: ~root@k8-0:~#
?2004h0;root@k8-0: ~root@k8-0:~# cp /etc/kubernetes/KcKontroller-manager.confKadmiKn.conf .
?2004h0;root@k8-0: ~root@k8-0:~# ls
admin.conf  kubeadm-config.yaml
?2004h0;root@k8-0: ~root@k8-0:~# kubectl
kubectl controls the Kubernetes cluster manager.

 Find more information at: https://kubernetes.io/docs/reference/kubectl/

Basic Commands (Beginner):
  create	  Create a resource from a file or from stdin
  expose	  Take a replication controller, service, deployment or pod and expose it as a new Kubernetes service
  run		  Run a particular image on the cluster
  set		  Set specific features on objects

Basic Commands (Intermediate):
  explain	  Get documentation for a resource
  get		  Display one or many resources
  edit		  Edit a resource on the server
  delete	  Delete resources by file names, stdin, resources and names, or by resources and label selector

Deploy Commands:
  rollout	  Manage the rollout of a resource
  scale		  Set a new size for a deployment, replica set, or replication controller
  autoscale	  Auto-scale a deployment, replica set, stateful set, or replication controller

Cluster Management Commands:
  certificate	  Modify certificate resources
  cluster-info	  Display cluster information
  top		  Display resource (CPU/memory) usage
  cordon	  Mark node as unschedulable
  uncordon	  Mark node as schedulable
  drain		  Drain node in preparation for maintenance
  taint		  Update the taints on one or more nodes

Troubleshooting and Debugging Commands:
  describe	  Show details of a specific resource or group of resources
  logs		  Print the logs for a container in a pod
  attach	  Attach to a running container
  exec		  Execute a command in a container
  port-forward	  Forward one or more local ports to a pod
  proxy		  Run a proxy to the Kubernetes API server
  cp		  Copy files and directories to and from containers
  auth		  Inspect authorization
  debug		  Create debugging sessions for troubleshooting workloads and nodes
  events	  List events

Advanced Commands:
  diff		  Diff the live version against a would-be applied version
  apply		  Apply a configuration to a resource by file name or stdin
  patch		  Update fields of a resource
  replace	  Replace a resource by file name or stdin
  wait		  Wait for a specific condition on one or many resources
  kustomize	  Build a kustomization target from a directory or URL

Settings Commands:
  label		  Update the labels on a resource
  annotate	  Update the annotations on a resource
  completion	  Output shell completion code for the specified shell (bash, zsh, fish, or powershell)

Subcommands provided by plugins:

Other Commands:
  alpha		  Commands for features in alpha
  api-resources	  Print the supported API resources on the server
  api-versions	  Print the supported API versions on the server, in the form of "group/version"
  config	  Modify kubeconfig files
  plugin	  Provides utilities for interacting with plugins
  version	  Print the client and server version information

Usage:
  kubectl [flags] [options]

Use "kubectl <command> --help" for more information about a given command.
Use "kubectl options" for a list of global command-line options (applies to all commands).
?2004h0;root@k8-0: ~root@k8-0:~# kubectl get nodes
E0214l04:37:34.464148  107778 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:37:34.465260  107778 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:37:34.467157  107778 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:37:34.468526  107778 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
E0214 04:37:34.468994  107778 memcache.go:265] "Unhandled Error" err="couldn't get current server API group list: Get \"http://localhost:8080/api?timeout=32s\": dial tcp [::1]:8080: connect: connection refused"
The connection to the server localhost:8080 was refused - did you specify the right host or port?
?2004h0;root@k8-0: ~root@k8-0:~# mkdir .kubnKe
?2004h0;root@k8-0: ~root@k8-0:~# cp kubeadm-config.yaml ./kubeadm-config.yamlK.kube/kubeadmiKconfig
?2004h0;root@k8-0: ~root@k8-0:~# ls -al .kube/
totall12
drwxr-xr-x 2 root root 4096 Feb 14 04:40 0m01;34m.0m
drwx------ 6 root root 4096 Feb 14 04:39 01;34m..0m
-rw-r--r-- 1 root root	646 Feb 14 04:40 config
?2004h0;root@k8-0: ~root@k8-0:~# kubectl get nodes -o wide
error: error loading config file "/root/.kube/config": no kind "ClusterConfiguration" is registered for version "kubeadm.k8s.io/v1beta4" in scheme "k8s.io/client-go/tools/clientcmd/api/latest/latest.go:50"
?2004h0;root@k8-0: ~root@k8-0:~# cp /etc/kubernetes/controller-manager.confKadmin.conf .kube/config
?2004h0;root@k8-0: ~root@k8-0:~# kubectl config view
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: DATA+OMITTED
    server: https://144.126.131.105:6443
  name: v-site-cluster
contexts:
- context:
    cluster: v-site-cluster
    user: kubernetes-admin
  name: kubernetes-admin@v-site-cluster
current-context: kubernetes-admin@v-site-cluster
kind: Config
users:
- name: kubernetes-admin
  user:
    client-certificate-data: DATA+OMITTED
    client-key-data: DATA+OMITTED
CCCCCCCCCCCCC17Pkubectlbgetenodesd-onwidefo.kube/config
NAME4l STATUS	  ROLES		  AGE	VERSION	  INTERNAL-IP	    EXTERNAL-IP	  OS-IMAGE	       KERNEL-VERSION	   CONTAINER-RUNTIME
k8-0   NotReady	  control-plane	  15m	v1.35.1	  144.126.131.105   <none>	  Ubuntu 24.04.4 LTS   6.8.0-100-generic   containerd://1.7.28
?2004h0;root@k8-0: ~root@k8-0:~# export KUBECONFIG=/root/.kube/c
cache/	config
0;root@k8-0: ~root@k8-0:~# export KUBECONFIG=/root/.kube/config
?2004h0;root@k8-0: ~root@k8-0:~# ## OK control plane up, loading cillium
?2004h0;root@k8-0: ~root@k8-0:~#
?2004h0;root@k8-0: ~root@k8-0:~# helm
The0Kubernetes package manager

Common actions for Helm:

- helm search:	  search for charts
- helm pull:	  download a chart to your local directory to view
- helm install:	  upload the chart to Kubernetes
- helm list:	  list releases of charts

Environment variables:

| Name				     | Description												  |
|------------------------------------|------------------------------------------------------------------------------------------------------------|
| $HELM_CACHE_HOME		     | set an alternative location for storing cached files.							  |
| $HELM_CONFIG_HOME		     | set an alternative location for storing Helm configuration.						  |
| $HELM_DATA_HOME		     | set an alternative location for storing Helm data.							  |
| $HELM_DEBUG			     | indicate whether or not Helm is running in Debug mode							  |
| $HELM_DRIVER			     | set the backend storage driver. Values are: configmap, secret, memory, sql.				  |
| $HELM_DRIVER_SQL_CONNECTION_STRING | set the connection string the SQL storage driver should use.						  |
| $HELM_MAX_HISTORY		     | set the maximum number of helm release history.								  |
| $HELM_NAMESPACE		     | set the namespace used for the helm operations.								  |
| $HELM_NO_PLUGINS		     | disable plugins. Set HELM_NO_PLUGINS=1 to disable plugins.						  |
| $HELM_PLUGINS			     | set the path to the plugins directory									  |
| $HELM_REGISTRY_CONFIG		     | set the path to the registry config file.								  |
| $HELM_REPOSITORY_CACHE	     | set the path to the repository cache directory								  |
| $HELM_REPOSITORY_CONFIG	     | set the path to the repositories file.									  |
| $KUBECONFIG			     | set an alternative Kubernetes configuration file (default "~/.kube/config")				  |
| $HELM_KUBEAPISERVER		     | set the Kubernetes API Server Endpoint for authentication						  |
| $HELM_KUBECAFILE		     | set the Kubernetes certificate authority file.								  |
| $HELM_KUBEASGROUPS		     | set the Groups to use for impersonation using a comma-separated list.					  |
| $HELM_KUBEASUSER		     | set the Username to impersonate for the operation.							  |
| $HELM_KUBECONTEXT		     | set the name of the kubeconfig context.									  |
| $HELM_KUBETOKEN		     | set the Bearer KubeToken used for authentication.							  |
| $HELM_KUBEINSECURE_SKIP_TLS_VERIFY | indicate if the Kubernetes API server's certificate validation should be skipped (insecure)		  |
| $HELM_KUBETLS_SERVER_NAME	     | set the server name used to validate the Kubernetes API server certificate				  |
| $HELM_BURST_LIMIT		     | set the default burst limit in the case the server contains many CRDs (default 100, -1 to disable)	  |
| $HELM_QPS			     | set the Queries Per Second in cases where a high number of calls exceed the option for higher burst values |
| $HELM_COLOR			     | set color output mode. Allowed values: never, always, auto (default: never)				  |
| $NO_COLOR			     | set to any non-empty value to disable all colored output (overrides $HELM_COLOR)				  |

Helm stores cache, configuration, and data based on the following configuration order:

- If a HELM_*_HOME environment variable is set, it will be used
- Otherwise, on systems supporting the XDG base directory specification, the XDG variables will be used
- When no other location is set a default location will be used based on the operating system

By default, the default directories depend on the Operating System. The defaults are listed below:

| Operating System | Cache Path		       | Configuration Path		| Data Path		  |
|------------------|---------------------------|--------------------------------|-------------------------|
| Linux		   | $HOME/.cache/helm	       | $HOME/.config/helm		| $HOME/.local/share/helm |
| macOS		   | $HOME/Library/Caches/helm | $HOME/Library/Preferences/helm | $HOME/Library/helm	  |
| Windows	   | %TEMP%\helm	       | %APPDATA%\helm			| %APPDATA%\helm	  |

Usage:
  helm [command]

Available Commands:
  completion  generate autocompletion scripts for the specified shell
  create      create a new chart with the given name
  dependency  manage a chart's dependencies
  env	      helm client environment information
  get	      download extended information of a named release
  help	      Help about any command
  history     fetch release history
  install     install a chart
  lint	      examine a chart for possible issues
  list	      list releases
  package     package a chart directory into a chart archive
  plugin      install, list, or uninstall Helm plugins
  pull	      download a chart from a repository and (optionally) unpack it in local directory
  push	      push a chart to remote
  registry    login to or logout from a registry
  repo	      add, list, remove, update, and index chart repositories
  rollback    roll back a release to a previous revision
  search      search for a keyword in charts
  show	      show information of a chart
  status      display the status of the named release
  template    locally render templates
  test	      run tests for a release
  uninstall   uninstall a release
  upgrade     upgrade a release
  verify      verify that a chart at the given path has been signed and is valid
  version     print the helm version information

Flags:
      --burst-limit int			client-side default throttling limit (default 100)
      --color string			use colored output (never, auto, always) (default "auto")
      --colour string			use colored output (never, auto, always) (default "auto")
      --content-cache string		path to the directory containing cached content (e.g. charts) (default "/root/.cache/helm/content")
      --debug				enable verbose output
  -h, --help				help for helm
      --kube-apiserver string		the address and the port for the Kubernetes API server
      --kube-as-group stringArray	group to impersonate for the operation, this flag can be repeated to specify multiple groups.
      --kube-as-user string		username to impersonate for the operation
      --kube-ca-file string		the certificate authority file for the Kubernetes API server connection
      --kube-context string		name of the kubeconfig context to use
      --kube-insecure-skip-tls-verify	if true, the Kubernetes API server's certificate will not be checked for validity. This will make your HTTPS connections insecure
      --kube-tls-server-name string	server name to use for Kubernetes API server certificate validation. If it is not provided, the hostname used to contact the server is used
      --kube-token string		bearer token used for authentication
      --kubeconfig string		path to the kubeconfig file
  -n, --namespace string		namespace scope for this request
      --qps float32			queries per second used when communicating with the Kubernetes API, not including bursting
      --registry-config string		path to the registry config file (default "/root/.config/helm/registry/config.json")
      --repository-cache string		path to the directory containing cached repository indexes (default "/root/.cache/helm/repository")
      --repository-config string	path to the file containing repository names and URLs (default "/root/.config/helm/repositories.yaml")

Use "helm [command] --help" for more information about a command.
?2004h0;root@k8-0: ~root@k8-0:~# 7mhelm repo add cilium https://helm.cilium.io/27m
7mhelm repo update27m
AACCCCCCCCCCCCChelm repo add cilium https://helm.cilium.io/
helm repo update
A
"cilium" has been added to your repositories
Hang tight while we grab the latest from your chart repositories...
...Successfully got an update from the "cilium" chart repository
Update Complete. ⎈Happy Helming!⎈
?2004h0;root@k8-0: ~root@k8-0:~# ip addr
1:0lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host noprefixroute
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:50:56:49:71:ab brd ff:ff:ff:ff:ff:ff
    altname enp0s18
    inet 144.126.131.105/20 brd 144.126.143.255 scope global eth0
       valid_lft forever preferred_lft forever
    inet6 2605:a140:2114:6820::1/64 scope global
       valid_lft forever preferred_lft forever
    inet6 fe80::250:56ff:fe49:71ab/64 scope link
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 1a:4f:e1:ef:c1:2d brd ff:ff:ff:ff:ff:ff
    altname enp0s19
    inet 10.0.0.3/22 brd 10.0.3.255 scope global eth1
       valid_lft forever preferred_lft forever
    inet6 fe80::184f:e1ff:feef:c12d/64 scope link
       valid_lft forever preferred_lft forever
?2004h0;root@k8-0: ~root@k8-0:~# 7mhelm upgrade --install cilium cilium/cilium \27m
7m  --namespace kube-system \27m
7m  --create-namespace \27m
7m  --set ipam.mode=kubernetes \27m
7m  --set ipam.operator.clusterPoolIPv4PodCIDRList[0]=10.200.0.0/16 \27m
7m  --set k8sServiceHost=207.244.237.219 \27m
7m  --set k8sServicePort=644327m
AAAAAAACCCCCCCCCCCCChelm upgrade --install cilium cilium/cilium \
  --namespace kube-system \
  --create-namespace \
  --set ipam.mode=kubernetes \
  --set ipam.operator.clusterPoolIPv4PodCIDRList[0]=10.200.0.0/16 \
  --set k8sServiceHost=207.244.237.219 \
ACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC111111111111111P144.126.131.105CC
CCCCCCCCCCCCCCCCCCCCCCCCCCC
A
Release "cilium" does not exist. Installing it now.
NAME: cilium
LAST DEPLOYED: Sat Feb 14 04:49:34 2026
NAMESPACE: 36mkube-system0m
STATUS: 32mdeployed0m
REVISION: 1
DESCRIPTION: Install complete
TEST SUITE: None
NOTES:
You have successfully installed Cilium with Hubble.

Your release version is 1.19.0.

For any further help, visit https://docs.cilium.io/en/v1.19/gettinghelp
?2004h0;root@k8-0: ~root@k8-0:~#
?2004h0;root@k8-0: ~root@k8-0:~# ##had to change the IP address from thgeKe template given...
?2004h0;root@k8-0: ~root@k8-0:~# 7mkubectl get pods -n kube-system -w27m
7mkubectl get nodes -o wide27m
AACCCCCCCCCCCCCkubectl get pods -n kube-system -w
kubectl get nodes -o wide
A
NAME4l				   READY   STATUS    RESTARTS	AGE
cilium-envoy-5xwt5		   1/1	   Running   0		4m8s
cilium-n9vnl			   1/1	   Running   0		4m8s
cilium-operator-67888fff84-5msf7   1/1	   Running   0		4m8s
cilium-operator-67888fff84-w4zrt   0/1	   Pending   0		4m8s
coredns-7d764666f9-qw944	   1/1	   Running   0		25m
coredns-7d764666f9-vdpsf	   1/1	   Running   0		25m
etcd-k8-0			   1/1	   Running   0		25m
kube-apiserver-k8-0		   1/1	   Running   0		25m
kube-controller-manager-k8-0	   1/1	   Running   0		25m
kube-proxy-4b45f		   1/1	   Running   0		25m
kube-scheduler-k8-0		   1/1	   Running   0		25m

^CNAME	 STATUS	  ROLES		  AGE	VERSION	  INTERNAL-IP	    EXTERNAL-IP	  OS-IMAGE	       KERNEL-VERSION	   CONTAINER-RUNTIME
k8-0   Ready	control-plane	26m   v1.35.1	144.126.131.105	  <none>	Ubuntu 24.04.4 LTS   6.8.0-100-generic	 containerd://1.7.28
?2004h0;root@k8-0: ~root@k8-0:~# kubectl get nodes -o wide
NAME4l STATUS	ROLES		AGE   VERSION	INTERNAL-IP	  EXTERNAL-IP	OS-IMAGE	     KERNEL-VERSION	 CONTAINER-RUNTIME
k8-0   Ready	control-plane	26m   v1.35.1	144.126.131.105	  <none>	Ubuntu 24.04.4 LTS   6.8.0-100-generic	 containerd://1.7.28
?2004h0;root@k8-0: ~root@k8-0:~# kubectl get nodes -o wide
NAME4l STATUS	ROLES		AGE   VERSION	INTERNAL-IP	  EXTERNAL-IP	OS-IMAGE	     KERNEL-VERSION	 CONTAINER-RUNTIME
k8-0   Ready	control-plane	27m   v1.35.1	144.126.131.105	  <none>	Ubuntu 24.04.4 LTS   6.8.0-100-generic	 containerd://1.7.28
CCCCCCCCCCCCC23Pkubectlhgetepods -nbkube-systemm-wheotemplatetgiven...
NAME4l				   READY   STATUS    RESTARTS	AGE
cilium-envoy-5xwt5		   1/1	   Running   0		5m47s
cilium-n9vnl			   1/1	   Running   0		5m47s
cilium-operator-67888fff84-5msf7   1/1	   Running   0		5m47s
cilium-operator-67888fff84-w4zrt   0/1	   Pending   0		5m47s
coredns-7d764666f9-qw944	   1/1	   Running   0		27m
coredns-7d764666f9-vdpsf	   1/1	   Running   0		27m
etcd-k8-0			   1/1	   Running   0		27m
kube-apiserver-k8-0		   1/1	   Running   0		27m
kube-controller-manager-k8-0	   1/1	   Running   0		27m
kube-proxy-4b45f		   1/1	   Running   0		27m
kube-scheduler-k8-0		   1/1	   Running   0		27m

/
^C?2004h0;root@k8-0: ~root@k8-0:~# kubectl get pods -n kube-system -w
NAME4l				   READY   STATUS    RESTARTS	AGE
cilium-envoy-5xwt5		   1/1	   Running   0		6m58s
cilium-n9vnl			   1/1	   Running   0		6m58s
cilium-operator-67888fff84-5msf7   1/1	   Running   0		6m58s
cilium-operator-67888fff84-w4zrt   0/1	   Pending   0		6m58s
coredns-7d764666f9-qw944	   1/1	   Running   0		28m
coredns-7d764666f9-vdpsf	   1/1	   Running   0		28m
etcd-k8-0			   1/1	   Running   0		28m
kube-apiserver-k8-0		   1/1	   Running   0		28m
kube-controller-manager-k8-0	   1/1	   Running   0		28m
kube-proxy-4b45f		   1/1	   Running   0		28m
kube-scheduler-k8-0		   1/1	   Running   0		28m
^C?2004h0;root@k8-0: ~root@k8-0:~# kubectl get pods -n kube-system -K
NAME4l				   READY   STATUS    RESTARTS	AGE
cilium-envoy-5xwt5		   1/1	   Running   0		7m10s
cilium-n9vnl			   1/1	   Running   0		7m10s
cilium-operator-67888fff84-5msf7   1/1	   Running   0		7m10s
cilium-operator-67888fff84-w4zrt   0/1	   Pending   0		7m10s
coredns-7d764666f9-qw944	   1/1	   Running   0		28m
coredns-7d764666f9-vdpsf	   1/1	   Running   0		28m
etcd-k8-0			   1/1	   Running   0		28m
kube-apiserver-k8-0		   1/1	   Running   0		28m
kube-controller-manager-k8-0	   1/1	   Running   0		28m
kube-proxy-4b45f		   1/1	   Running   0		28m
kube-scheduler-k8-0		   1/1	   Running   0		28m
?2004h0;root@k8-0: ~root@k8-0:~# kubectl get pods -n kube-system -w
NAME4l				   READY   STATUS    RESTARTS	AGE
cilium-envoy-5xwt5		   1/1	   Running   0		7m14s
cilium-n9vnl			   1/1	   Running   0		7m14s
cilium-operator-67888fff84-5msf7   1/1	   Running   0		7m14s
cilium-operator-67888fff84-w4zrt   0/1	   Pending   0		7m14s
coredns-7d764666f9-qw944	   1/1	   Running   0		28m
coredns-7d764666f9-vdpsf	   1/1	   Running   0		28m
etcd-k8-0			   1/1	   Running   0		28m
kube-apiserver-k8-0		   1/1	   Running   0		28m
kube-controller-manager-k8-0	   1/1	   Running   0		28m
kube-proxy-4b45f		   1/1	   Running   0		28m
kube-scheduler-k8-0		   1/1	   Running   0		28m
^C?2004h0;root@k8-0: ~root@k8-0:~# ## Smoke test pod creation
?2004h0;root@k8-0: ~root@k8-0:~# 7mkubectl create deployment nginx --image=nginx --replicas=227m
7mkubectl expose deployment nginx --port=80 --target-port=8027m
7mkubectl get pods -o wide27m
7mkubectl get svc nginx27m
AAAACCCCCCCCCCCCCkubectl create deployment nginx --image=nginx --replicas=2
kubectl expose deployment nginx --port=80 --target-port=80
kubectl get pods -o wide
kubectl get svc nginx
A
deployment.apps/nginx created
service/nginx exposed
NAME			 READY	 STATUS	   RESTARTS   AGE   IP	     NODE     NOMINATED NODE   READINESS GATES
nginx-56c45fd5ff-4fx4b	 0/1	 Pending   0	      1s    <none>   <none>   <none>	       <none>
nginx-56c45fd5ff-l676j	 0/1	 Pending   0	      1s    <none>   <none>   <none>	       <none>
NAME	TYPE	    CLUSTER-IP	    EXTERNAL-IP	  PORT(S)   AGE
nginx	ClusterIP   10.102.81.242   <none>	  80/TCP    1s
?2004h0;root@k8-0: ~root@k8-0:~# kgp
Command 'kgp' not found, did you mean:
  command 'kup' from deb kup-client (0.3.6-2.1)
  command 'kgx' from deb gnome-console (45.0-1)
  command 'pgp' from deb pgpgpg (0.13-12)
  command 'kgb' from deb kgb (1.0b4+ds-14build1)
  command 'kgpg' from deb kgpg (4:23.08.4-0ubuntu1)
  command 'lgp' from deb simh (3.8.1-6.1)
  command 'mgp' from deb mgp (1.13a+upstream20090219-12)
  command 'gp' from deb pari-gp (2.15.4-2)
Try: apt install <deb name>
?2004h0;root@k8-0: ~root@k8-0:~# kubernKectl gKet pods -o wide
NAME4l			 READY	 STATUS	   RESTARTS   AGE   IP	     NODE     NOMINATED NODE   READINESS GATES
nginx-56c45fd5ff-4fx4b	 0/1	 Pending   0	      35s   <none>   <none>   <none>	       <none>
nginx-56c45fd5ff-l676j	 0/1	 Pending   0	      35s   <none>   <none>   <none>	       <none>
?2004h0;root@k8-0: ~root@k8-0:~# 7mkubectl get pods -A27m
7mkubectl describe pod -n kube-system -l k8s-app=cilium27m
7mkubectl describe pod -n kube-system -l k8s-app=kube-dns27m
AAACCCCCCCCCCCCCkubectl get pods -A
kubectl describe pod -n kube-system -l k8s-app=cilium
kubectl describe pod -n kube-system -l k8s-app=kube-dns
A
NAMESPACE     NAME				 READY	 STATUS	   RESTARTS   AGE
default	      nginx-56c45fd5ff-4fx4b		 0/1	 Pending   0	      2m17s
default	      nginx-56c45fd5ff-l676j		 0/1	 Pending   0	      2m17s
kube-system   cilium-envoy-5xwt5		 1/1	 Running   0	      10m
kube-system   cilium-n9vnl			 1/1	 Running   0	      10m
kube-system   cilium-operator-67888fff84-5msf7	 1/1	 Running   0	      10m
kube-system   cilium-operator-67888fff84-w4zrt	 0/1	 Pending   0	      10m
kube-system   coredns-7d764666f9-qw944		 1/1	 Running   0	      31m
kube-system   coredns-7d764666f9-vdpsf		 1/1	 Running   0	      31m
kube-system   etcd-k8-0				 1/1	 Running   0	      31m
kube-system   kube-apiserver-k8-0		 1/1	 Running   0	      32m
kube-system   kube-controller-manager-k8-0	 1/1	 Running   0	      31m
kube-system   kube-proxy-4b45f			 1/1	 Running   0	      31m
kube-system   kube-scheduler-k8-0		 1/1	 Running   0	      31m
Name:		      cilium-n9vnl
Namespace:	      kube-system
Priority:	      2000001000
Priority Class Name:  system-node-critical
Service Account:      cilium
Node:		      k8-0/144.126.131.105
Start Time:	      Sat, 14 Feb 2026 04:49:36 +0100
Labels:		      app.kubernetes.io/name=cilium-agent
		      app.kubernetes.io/part-of=cilium
		      controller-revision-hash=5ccb56d487
		      k8s-app=cilium
		      pod-template-generation=1
Annotations:	      kubectl.kubernetes.io/default-container: cilium-agent
Status:		      Running
SeccompProfile:	      Unconfined
IP:		      144.126.131.105
IPs:
  IP:		144.126.131.105
Controlled By:	DaemonSet/cilium
Init Containers:
  config:
    Container ID:  containerd://98804b692ebc2023f1bda09b2313b68e1744c37b698a08c873fe0432c959cbce
    Image:	   quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Image ID:	   quay.io/cilium/cilium@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Port:	   <none>
    Host Port:	   <none>
    Command:
      cilium-dbg
      build-config
    State:	    Terminated
      Reason:	    Completed
      Exit Code:    0
      Started:	    Sat, 14 Feb 2026 04:49:54 +0100
      Finished:	    Sat, 14 Feb 2026 04:49:55 +0100
    Ready:	    True
    Restart Count:  0
    Environment:
      K8S_NODE_NAME:		 (v1:spec.nodeName)
      CILIUM_K8S_NAMESPACE:	kube-system (v1:metadata.namespace)
      KUBERNETES_SERVICE_HOST:	144.126.131.105
      KUBERNETES_SERVICE_PORT:	6443
    Mounts:
      /tmp from tmp (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-chcrx (ro)
  mount-cgroup:
    Container ID:  containerd://be6ef8b7171c967f00b756ae42e33a498e12323987dc77df9b5f56bfb6404636
    Image:	   quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Image ID:	   quay.io/cilium/cilium@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Port:	   <none>
    Host Port:	   <none>
    Command:
      sh
      -ec
      cp /usr/bin/cilium-mount /hostbin/cilium-mount;
      nsenter --cgroup=/hostproc/1/ns/cgroup --mount=/hostproc/1/ns/mnt "${BIN_PATH}/cilium-mount" $CGROUP_ROOT;
      rm /hostbin/cilium-mount

    State:	    Terminated
      Reason:	    Completed
      Exit Code:    0
      Started:	    Sat, 14 Feb 2026 04:49:56 +0100
      Finished:	    Sat, 14 Feb 2026 04:49:56 +0100
    Ready:	    True
    Restart Count:  0
    Environment:
      CGROUP_ROOT:  /run/cilium/cgroupv2
      BIN_PATH:	    /opt/cni/bin
    Mounts:
      /hostbin from cni-path (rw)
      /hostproc from hostproc (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-chcrx (ro)
  apply-sysctl-overwrites:
    Container ID:  containerd://638a1b83b5c13caed8271ffe474375da2c05d80a0019cc07edd432555305a7c5
    Image:	   quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Image ID:	   quay.io/cilium/cilium@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Port:	   <none>
    Host Port:	   <none>
    Command:
      sh
      -ec
      cp /usr/bin/cilium-sysctlfix /hostbin/cilium-sysctlfix;
      nsenter --mount=/hostproc/1/ns/mnt "${BIN_PATH}/cilium-sysctlfix";
      rm /hostbin/cilium-sysctlfix

    State:	    Terminated
      Reason:	    Completed
      Exit Code:    0
      Started:	    Sat, 14 Feb 2026 04:49:57 +0100
      Finished:	    Sat, 14 Feb 2026 04:49:57 +0100
    Ready:	    True
    Restart Count:  0
    Environment:
      BIN_PATH:	 /opt/cni/bin
    Mounts:
      /hostbin from cni-path (rw)
      /hostproc from hostproc (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-chcrx (ro)
  mount-bpf-fs:
    Container ID:  containerd://d6d2f4a4fefa27a307148f5eac912ec36a34ea6ff3038beb60e77b742ae0b3e1
    Image:	   quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Image ID:	   quay.io/cilium/cilium@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Port:	   <none>
    Host Port:	   <none>
    Command:
      /bin/bash
      -c
      --
    Args:
      mount | grep "/sys/fs/bpf type bpf" || mount -t bpf bpf /sys/fs/bpf
    State:	    Terminated
      Reason:	    Completed
      Exit Code:    0
      Started:	    Sat, 14 Feb 2026 04:49:58 +0100
      Finished:	    Sat, 14 Feb 2026 04:49:58 +0100
    Ready:	    True
    Restart Count:  0
    Environment:    <none>
    Mounts:
      /sys/fs/bpf from bpf-maps (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-chcrx (ro)
  clean-cilium-state:
    Container ID:  containerd://f47e7c858212ea56f9355e2b417177459cc99468b8c4a6c5521f90acf4948c6e
    Image:	   quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Image ID:	   quay.io/cilium/cilium@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Port:	   <none>
    Host Port:	   <none>
    Command:
      /init-container.sh
    State:	    Terminated
      Reason:	    Completed
      Exit Code:    0
      Started:	    Sat, 14 Feb 2026 04:49:59 +0100
      Finished:	    Sat, 14 Feb 2026 04:49:59 +0100
    Ready:	    True
    Restart Count:  0
    Environment:
      CILIUM_ALL_STATE:		  <set to the key 'clean-cilium-state' of config map 'cilium-config'>	      Optional: true
      CILIUM_BPF_STATE:		  <set to the key 'clean-cilium-bpf-state' of config map 'cilium-config'>     Optional: true
      WRITE_CNI_CONF_WHEN_READY:  <set to the key 'write-cni-conf-when-ready' of config map 'cilium-config'>  Optional: true
      KUBERNETES_SERVICE_HOST:	  144.126.131.105
      KUBERNETES_SERVICE_PORT:	  6443
    Mounts:
      /run/cilium/cgroupv2 from cilium-cgroup (rw)
      /sys/fs/bpf from bpf-maps (rw)
      /var/run/cilium from cilium-run (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-chcrx (ro)
  install-cni-binaries:
    Container ID:  containerd://bc4f6fe7e92848c89878937c207ea17351d4557ecefa3f55555f4c372ef9707e
    Image:	   quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Image ID:	   quay.io/cilium/cilium@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Port:	   <none>
    Host Port:	   <none>
    Command:
      /install-plugin.sh
    State:	    Terminated
      Reason:	    Completed
      Exit Code:    0
      Started:	    Sat, 14 Feb 2026 04:50:00 +0100
      Finished:	    Sat, 14 Feb 2026 04:50:00 +0100
    Ready:	    True
    Restart Count:  0
    Limits:
      cpu:     1
      memory:  1Gi
    Requests:
      cpu:	  100m
      memory:	  10Mi
    Environment:  <none>
    Mounts:
      /host/opt/cni/bin from cni-path (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-chcrx (ro)
Containers:
  cilium-agent:
    Container ID:  containerd://9afc14fce4465591b1cee095a64a9d9c25bdf7aa94740dc72438caadbeae711a
    Image:	   quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Image ID:	   quay.io/cilium/cilium@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60
    Ports:	   9879/TCP (health), 4244/TCP (peer-service)
    Host Ports:	   9879/TCP (health), 4244/TCP (peer-service)
    Command:
      cilium-agent
    Args:
      --config-dir=/tmp/cilium/config-map
    State:	    Running
      Started:	    Sat, 14 Feb 2026 04:50:02 +0100
    Ready:	    True
    Restart Count:  0
    Liveness:	    http-get http://127.0.0.1:health/healthz delay=0s timeout=5s period=30s #success=1 #failure=10
    Readiness:	    http-get http://127.0.0.1:health/healthz delay=0s timeout=5s period=30s #success=1 #failure=3
    Startup:	    http-get http://127.0.0.1:health/healthz delay=5s timeout=1s period=2s #success=1 #failure=300
    Environment:
      K8S_NODE_NAME:		      (v1:spec.nodeName)
      CILIUM_K8S_NAMESPACE:	     kube-system (v1:metadata.namespace)
      CILIUM_CLUSTERMESH_CONFIG:     /var/lib/cilium/clustermesh/
      GOMEMLIMIT:		     node allocatable (limits.memory)
      KUBERNETES_SERVICE_HOST:	     144.126.131.105
      KUBERNETES_SERVICE_PORT:	     6443
      KUBE_CLIENT_BACKOFF_BASE:	     1
      KUBE_CLIENT_BACKOFF_DURATION:  120
    Mounts:
      /host/etc/cni/net.d from etc-cni-netd (rw)
      /host/proc/sys/kernel from host-proc-sys-kernel (rw)
      /host/proc/sys/net from host-proc-sys-net (rw)
      /lib/modules from lib-modules (ro)
      /run/xtables.lock from xtables-lock (rw)
      /sys/fs/bpf from bpf-maps (rw)
      /tmp from tmp (rw)
      /var/lib/cilium/clustermesh from clustermesh-secrets (ro)
      /var/lib/cilium/tls/hubble from hubble-tls (ro)
      /var/run/cilium from cilium-run (rw)
      /var/run/cilium/envoy/sockets from envoy-sockets (rw)
      /var/run/cilium/netns from cilium-netns (rw)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-chcrx (ro)
Conditions:
  Type			      Status
  PodReadyToStartContainers   True
  Initialized		      True
  Ready			      True
  ContainersReady	      True
  PodScheduled		      True
Volumes:
  tmp:
    Type:	EmptyDir (a temporary directory that shares a pod's lifetime)
    Medium:
    SizeLimit:	<unset>
  cilium-run:
    Type:	   HostPath (bare host directory volume)
    Path:	   /var/run/cilium
    HostPathType:  DirectoryOrCreate
  cilium-netns:
    Type:	   HostPath (bare host directory volume)
    Path:	   /var/run/netns
    HostPathType:  DirectoryOrCreate
  bpf-maps:
    Type:	   HostPath (bare host directory volume)
    Path:	   /sys/fs/bpf
    HostPathType:  DirectoryOrCreate
  hostproc:
    Type:	   HostPath (bare host directory volume)
    Path:	   /proc
    HostPathType:  Directory
  cilium-cgroup:
    Type:	   HostPath (bare host directory volume)
    Path:	   /run/cilium/cgroupv2
    HostPathType:  DirectoryOrCreate
  cni-path:
    Type:	   HostPath (bare host directory volume)
    Path:	   /opt/cni/bin
    HostPathType:  DirectoryOrCreate
  etc-cni-netd:
    Type:	   HostPath (bare host directory volume)
    Path:	   /etc/cni/net.d
    HostPathType:  DirectoryOrCreate
  lib-modules:
    Type:	   HostPath (bare host directory volume)
    Path:	   /lib/modules
    HostPathType:
  xtables-lock:
    Type:	   HostPath (bare host directory volume)
    Path:	   /run/xtables.lock
    HostPathType:  FileOrCreate
  envoy-sockets:
    Type:	   HostPath (bare host directory volume)
    Path:	   /var/run/cilium/envoy/sockets
    HostPathType:  DirectoryOrCreate
  clustermesh-secrets:
    Type:	 Projected (a volume that contains injected data from multiple sources)
    SecretName:	 cilium-clustermesh
    Optional:	 true
    SecretName:	 clustermesh-apiserver-remote-cert
    Optional:	 true
    SecretName:	 clustermesh-apiserver-local-cert
    Optional:	 true
  host-proc-sys-net:
    Type:	   HostPath (bare host directory volume)
    Path:	   /proc/sys/net
    HostPathType:  Directory
  host-proc-sys-kernel:
    Type:	   HostPath (bare host directory volume)
    Path:	   /proc/sys/kernel
    HostPathType:  Directory
  hubble-tls:
    Type:	 Projected (a volume that contains injected data from multiple sources)
    SecretName:	 hubble-server-certs
    Optional:	 true
  kube-api-access-chcrx:
    Type:		     Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:	     kube-root-ca.crt
    Optional:		     false
    DownwardAPI:	     true
QoS Class:		     Burstable
Node-Selectors:		     kubernetes.io/os=linux
Tolerations:		     op=Exists
			     node.kubernetes.io/disk-pressure:NoSchedule op=Exists
			     node.kubernetes.io/memory-pressure:NoSchedule op=Exists
			     node.kubernetes.io/network-unavailable:NoSchedule op=Exists
			     node.kubernetes.io/not-ready:NoExecute op=Exists
			     node.kubernetes.io/pid-pressure:NoSchedule op=Exists
			     node.kubernetes.io/unreachable:NoExecute op=Exists
			     node.kubernetes.io/unschedulable:NoSchedule op=Exists
Events:
  Type	   Reason	     Age		  From		     Message
  ----	   ------	     ----		  ----		     -------
  Normal   Scheduled	     10m		  default-scheduler  Successfully assigned kube-system/cilium-n9vnl to k8-0
  Normal   Pulling	     10m		  kubelet	     spec.initContainers{config}: Pulling image "quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60"
  Normal   Pulled	     10m		  kubelet	     spec.initContainers{config}: Successfully pulled image "quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60" in 18.037s (18.038s including waiting). Image size: 257743861 bytes.
  Normal   Created	     10m		  kubelet	     spec.initContainers{config}: Container created
  Normal   Started	     10m		  kubelet	     spec.initContainers{config}: Container started
  Normal   Pulled	     10m		  kubelet	     spec.initContainers{mount-cgroup}: Container image "quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60" already present on machine and can be accessed by the pod
  Normal   Created	     10m		  kubelet	     spec.initContainers{mount-cgroup}: Container created
  Normal   Started	     10m		  kubelet	     spec.initContainers{mount-cgroup}: Container started
  Normal   Started	     10m		  kubelet	     spec.initContainers{apply-sysctl-overwrites}: Container started
  Normal   Pulled	     10m		  kubelet	     spec.initContainers{apply-sysctl-overwrites}: Container image "quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60" already present on machine and can be accessed by the pod
  Normal   Created	     10m		  kubelet	     spec.initContainers{apply-sysctl-overwrites}: Container created
  Normal   Pulled	     10m		  kubelet	     spec.initContainers{mount-bpf-fs}: Container image "quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60" already present on machine and can be accessed by the pod
  Normal   Created	     10m		  kubelet	     spec.initContainers{mount-bpf-fs}: Container created
  Normal   Started	     10m		  kubelet	     spec.initContainers{mount-bpf-fs}: Container started
  Normal   Started	     10m		  kubelet	     spec.initContainers{clean-cilium-state}: Container started
  Normal   Pulled	     10m		  kubelet	     spec.initContainers{clean-cilium-state}: Container image "quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60" already present on machine and can be accessed by the pod
  Normal   Created	     10m		  kubelet	     spec.initContainers{clean-cilium-state}: Container created
  Normal   Pulled	     10m		  kubelet	     spec.initContainers{install-cni-binaries}: Container image "quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60" already present on machine and can be accessed by the pod
  Normal   Created	     10m		  kubelet	     spec.initContainers{install-cni-binaries}: Container created
  Normal   Started	     10m		  kubelet	     spec.initContainers{install-cni-binaries}: Container started
  Normal   Pulled	     10m		  kubelet	     spec.containers{cilium-agent}: Container image "quay.io/cilium/cilium:v1.19.0@sha256:be9f8571c2e114b3e12e41f785f2356ade703b2eac936aa878805565f0468c60" already present on machine and can be accessed by the pod
  Normal   Created	     10m		  kubelet	     spec.containers{cilium-agent}: Container created
  Normal   Started	     10m		  kubelet	     spec.containers{cilium-agent}: Container started
  Warning  Unhealthy	     9m58s (x5 over 10m)  kubelet	     spec.containers{cilium-agent}: Startup probe failed: Get "http://127.0.0.1:9879/healthz": dial tcp 127.0.0.1:9879: connect: connection refused
  Warning  Unhealthy	     9m56s		  kubelet	     spec.containers{cilium-agent}: Startup probe failed: HTTP probe failed with statuscode: 503
  Warning  DNSConfigForming  3m7s (x20 over 10m)  kubelet	     Nameserver limits were exceeded, some nameservers have been omitted, the applied nameserver line is: 209.126.15.51 209.126.15.52 2605:a140:5028::1:53
Name:		      coredns-7d764666f9-qw944
Namespace:	      kube-system
Priority:	      2000000000
Priority Class Name:  system-cluster-critical
Service Account:      coredns
Node:		      k8-0/144.126.131.105
Start Time:	      Sat, 14 Feb 2026 04:50:26 +0100
Labels:		      k8s-app=kube-dns
		      pod-template-hash=7d764666f9
Annotations:	      <none>
Status:		      Running
IP:		      10.200.0.175
IPs:
  IP:		10.200.0.175
Controlled By:	ReplicaSet/coredns-7d764666f9
Containers:
  coredns:
    Container ID:  containerd://c4a43f04de073425956491aef42db11bfda9620d129ac788880172cf536f55bf
    Image:	   registry.k8s.io/coredns/coredns:v1.13.1
    Image ID:	   registry.k8s.io/coredns/coredns@sha256:9b9128672209474da07c91439bf15ed704ae05ad918dd6454e5b6ae14e35fee6
    Ports:	   53/UDP (dns), 53/TCP (dns-tcp), 9153/TCP (metrics), 8080/TCP (liveness-probe), 8181/TCP (readiness-probe)
    Host Ports:	   0/UDP (dns), 0/TCP (dns-tcp), 0/TCP (metrics), 0/TCP (liveness-probe), 0/TCP (readiness-probe)
    Args:
      -conf
      /etc/coredns/Corefile
    State:	    Running
      Started:	    Sat, 14 Feb 2026 04:50:27 +0100
    Ready:	    True
    Restart Count:  0
    Limits:
      memory:  170Mi
    Requests:
      cpu:	  100m
      memory:	  70Mi
    Liveness:	  http-get http://:liveness-probe/health delay=60s timeout=5s period=10s #success=1 #failure=5
    Readiness:	  http-get http://:readiness-probe/ready delay=0s timeout=1s period=10s #success=1 #failure=3
    Environment:  <none>
    Mounts:
      /etc/coredns from config-volume (ro)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-dfdqg (ro)
Conditions:
  Type			      Status
  PodReadyToStartContainers   True
  Initialized		      True
  Ready			      True
  ContainersReady	      True
  PodScheduled		      True
Volumes:
  config-volume:
    Type:      ConfigMap (a volume populated by a ConfigMap)
    Name:      coredns
    Optional:  false
  kube-api-access-dfdqg:
    Type:		     Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:	     kube-root-ca.crt
    Optional:		     false
    DownwardAPI:	     true
QoS Class:		     Burstable
Node-Selectors:		     kubernetes.io/os=linux
Tolerations:		     CriticalAddonsOnly op=Exists
			     node-role.kubernetes.io/control-plane:NoSchedule
			     node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
			     node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type	   Reason	     Age		   From		      Message
  ----	   ------	     ----		   ----		      -------
  Warning  FailedScheduling  11m (x5 over 31m)	   default-scheduler  0/1 nodes are available: 1 node(s) had untolerated taint(s). no new claims to deallocate, preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.
  Normal   Scheduled	     9m48s		   default-scheduler  Successfully assigned kube-system/coredns-7d764666f9-qw944 to k8-0
  Normal   Pulled	     9m47s		   kubelet	      spec.containers{coredns}: Container image "registry.k8s.io/coredns/coredns:v1.13.1" already present on machine and can be accessed by the pod
  Normal   Created	     9m47s		   kubelet	      spec.containers{coredns}: Container created
  Normal   Started	     9m47s		   kubelet	      spec.containers{coredns}: Container started
  Warning  DNSConfigForming  74s (x12 over 9m47s)  kubelet	      Nameserver limits were exceeded, some nameservers have been omitted, the applied nameserver line is: 209.126.15.51 209.126.15.52 2605:a140:5028::1:53


Name:		      coredns-7d764666f9-vdpsf
Namespace:	      kube-system
Priority:	      2000000000
Priority Class Name:  system-cluster-critical
Service Account:      coredns
Node:		      k8-0/144.126.131.105
Start Time:	      Sat, 14 Feb 2026 04:50:26 +0100
Labels:		      k8s-app=kube-dns
		      pod-template-hash=7d764666f9
Annotations:	      <none>
Status:		      Running
IP:		      10.200.0.201
IPs:
  IP:		10.200.0.201
Controlled By:	ReplicaSet/coredns-7d764666f9
Containers:
  coredns:
    Container ID:  containerd://5206c15b1cb3b3107c7eb61ecc9f8bd5afadbe8a1269b24d860d38b27a11a6f3
    Image:	   registry.k8s.io/coredns/coredns:v1.13.1
    Image ID:	   registry.k8s.io/coredns/coredns@sha256:9b9128672209474da07c91439bf15ed704ae05ad918dd6454e5b6ae14e35fee6
    Ports:	   53/UDP (dns), 53/TCP (dns-tcp), 9153/TCP (metrics), 8080/TCP (liveness-probe), 8181/TCP (readiness-probe)
    Host Ports:	   0/UDP (dns), 0/TCP (dns-tcp), 0/TCP (metrics), 0/TCP (liveness-probe), 0/TCP (readiness-probe)
    Args:
      -conf
      /etc/coredns/Corefile
    State:	    Running
      Started:	    Sat, 14 Feb 2026 04:50:27 +0100
    Ready:	    True
    Restart Count:  0
    Limits:
      memory:  170Mi
    Requests:
      cpu:	  100m
      memory:	  70Mi
    Liveness:	  http-get http://:liveness-probe/health delay=60s timeout=5s period=10s #success=1 #failure=5
    Readiness:	  http-get http://:readiness-probe/ready delay=0s timeout=1s period=10s #success=1 #failure=3
    Environment:  <none>
    Mounts:
      /etc/coredns from config-volume (ro)
      /var/run/secrets/kubernetes.io/serviceaccount from kube-api-access-m9bfw (ro)
Conditions:
  Type			      Status
  PodReadyToStartContainers   True
  Initialized		      True
  Ready			      True
  ContainersReady	      True
  PodScheduled		      True
Volumes:
  config-volume:
    Type:      ConfigMap (a volume populated by a ConfigMap)
    Name:      coredns
    Optional:  false
  kube-api-access-m9bfw:
    Type:		     Projected (a volume that contains injected data from multiple sources)
    TokenExpirationSeconds:  3607
    ConfigMapName:	     kube-root-ca.crt
    Optional:		     false
    DownwardAPI:	     true
QoS Class:		     Burstable
Node-Selectors:		     kubernetes.io/os=linux
Tolerations:		     CriticalAddonsOnly op=Exists
			     node-role.kubernetes.io/control-plane:NoSchedule
			     node.kubernetes.io/not-ready:NoExecute op=Exists for 300s
			     node.kubernetes.io/unreachable:NoExecute op=Exists for 300s
Events:
  Type	   Reason	     Age		   From		      Message
  ----	   ------	     ----		   ----		      -------
  Warning  FailedScheduling  11m (x5 over 31m)	   default-scheduler  0/1 nodes are available: 1 node(s) had untolerated taint(s). no new claims to deallocate, preemption: 0/1 nodes are available: 1 Preemption is not helpful for scheduling.
  Normal   Scheduled	     9m48s		   default-scheduler  Successfully assigned kube-system/coredns-7d764666f9-vdpsf to k8-0
  Normal   Pulled	     9m47s		   kubelet	      spec.containers{coredns}: Container image "registry.k8s.io/coredns/coredns:v1.13.1" already present on machine and can be accessed by the pod
  Normal   Created	     9m47s		   kubelet	      spec.containers{coredns}: Container created
  Normal   Started	     9m47s		   kubelet	      spec.containers{coredns}: Container started
  Warning  DNSConfigForming  66s (x12 over 9m47s)  kubelet	      Nameserver limits were exceeded, some nameservers have been omitted, the applied nameserver line is: 209.126.15.51 209.126.15.52 2605:a140:5028::1:53
?2004h0;root@k8-0: ~root@k8-0:~# 7mkubectl get nodes -o wide27m
7mkubectl get pods -A27m
AACCCCCCCCCCCCCkubectl get nodes -o wide
kubectl get pods -A
A
NAME4l STATUS	ROLES		AGE   VERSION	INTERNAL-IP	  EXTERNAL-IP	OS-IMAGE	     KERNEL-VERSION	 CONTAINER-RUNTIME
k8-0   Ready	control-plane	34m   v1.35.1	144.126.131.105	  <none>	Ubuntu 24.04.4 LTS   6.8.0-100-generic	 containerd://1.7.28
NAMESPACE     NAME				 READY	 STATUS	   RESTARTS   AGE
default	      nginx-56c45fd5ff-4fx4b		 0/1	 Pending   0	      4m22s
default	      nginx-56c45fd5ff-l676j		 0/1	 Pending   0	      4m22s
kube-system   cilium-envoy-5xwt5		 1/1	 Running   0	      12m
kube-system   cilium-n9vnl			 1/1	 Running   0	      12m
kube-system   cilium-operator-67888fff84-5msf7	 1/1	 Running   0	      12m
kube-system   cilium-operator-67888fff84-w4zrt	 0/1	 Pending   0	      12m
kube-system   coredns-7d764666f9-qw944		 1/1	 Running   0	      33m
kube-system   coredns-7d764666f9-vdpsf		 1/1	 Running   0	      33m
kube-system   etcd-k8-0				 1/1	 Running   0	      34m
kube-system   kube-apiserver-k8-0		 1/1	 Running   0	      34m
kube-system   kube-controller-manager-k8-0	 1/1	 Running   0	      34m
kube-system   kube-proxy-4b45f			 1/1	 Running   0	      33m
kube-system   kube-scheduler-k8-0		 1/1	 Running   0	      34m
?2004h0;root@k8-0: ~root@k8-0:~# 7mkubectl taint nodes k8-0 node-role.kubernetes.io/control-plane- || true27m
7mkubectl taint nodes k8-0 node-role.kubernetes.io/master- || true27m
AACCCCCCCCCCCCCkubectl taint nodes k8-0 node-role.kubernetes.io/control-plane- || true
kubectl taint nodes k8-0 node-role.kubernetes.io/master- || true
A
node/k8-0 untainted
error: taint "node-role.kubernetes.io/master" not found
CCCCCCCCCCCCCCCCCCCCCget@pods:-AKkubectl taint nodes k8-0 node-role.kubernetes.io/7@control-planeCCCCCCCCC
NAMESPACE     NAME				 READY	 STATUS	   RESTARTS   AGE
default	      nginx-56c45fd5ff-4fx4b		 1/1	 Running   0	      5m42s
default	      nginx-56c45fd5ff-l676j		 1/1	 Running   0	      5m42s
kube-system   cilium-envoy-5xwt5		 1/1	 Running   0	      14m
kube-system   cilium-n9vnl			 1/1	 Running   0	      14m
kube-system   cilium-operator-67888fff84-5msf7	 1/1	 Running   0	      14m
kube-system   cilium-operator-67888fff84-w4zrt	 0/1	 Pending   0	      14m
kube-system   coredns-7d764666f9-qw944		 1/1	 Running   0	      35m
kube-system   coredns-7d764666f9-vdpsf		 1/1	 Running   0	      35m
kube-system   etcd-k8-0				 1/1	 Running   0	      35m
kube-system   kube-apiserver-k8-0		 1/1	 Running   0	      35m
kube-system   kube-controller-manager-k8-0	 1/1	 Running   0	      35m
kube-system   kube-proxy-4b45f			 1/1	 Running   0	      35m
kube-system   kube-scheduler-k8-0		 1/1	 Running   0	      35m
?2004h0;root@k8-0: ~root@k8-0:~# ## HAd to untaint the control plane node
?2004h0;root@k8-0: ~root@k8-0:~# 7m# Exec into one nginx pod and curl the other27m
7mkubectl exec -it deploy/nginx -- curl -sS nginx27m
AACCCCCCCCCCCCC# Exec into one nginx pod and curl the other
kubectl exec -it deploy/nginx -- curl -sS nginx
A
<!DOCTYPE html>
<html>
<head>
<title>Welcome to nginx!</title>
<style>
html { color-scheme: light dark; }
body { width: 35em; margin: 0 auto;
font-family: Tahoma, Verdana, Arial, sans-serif; }
</style>
</head>
<body>
<h1>Welcome to nginx!</h1>
<p>If you see this page, the nginx web server is successfully installed and
working. Further configuration is required.</p>

<p>For online documentation and support please refer to
<a href="http://nginx.org/">nginx.org</a>.<br/>
Commercial support is available at
<a href="http://nginx.com/">nginx.com</a>.</p>

<p><em>Thank you for using nginx.</em></p>
</body>
</html>
?2004h0;root@k8-0: ~root@k8-0:~# pwd
/rootl
CCCCCCCCCCCCCCCCCCCCCCChttps://github.com/l0r3zz/k8-tools.gitom/l0r3zz/k8-tools.git27m
Command 'get' not found, but there are 18 similar ones.
?2004h0;root@k8-0: ~root@k8-0:~# C1P1@ione https://github.com/l0r3zz/k8-tools.git
Cloning into 'k8-tools'...
remote: Enumerating objects: 15, done.K
remote: Counting objects: 100% (15/15), done.K
remote: Compressing objects: 100% (11/11), done.K
remote: Total 15 (delta 3), reused 10 (delta 3), pack-reused 0 (from 0)K
Receiving objects: 100% (15/15), done.
Resolving deltas: 100% (3/3), done.
?2004h0;root@k8-0: ~root@k8-0:~# ls
admin.conf  0m01;34mk8-tools0m	kubeadm-config.yaml  01;34msnap0m
?2004h0;root@k8-0: ~root@k8-0:~# sourceeKe k8-tools/k8.sh
?2004hroot@k8-0:[2026-02-14 05:07:23]-#Bmkgp
NAME4l			 READY	 STATUS	   RESTARTS   AGE
nginx-56c45fd5ff-4fx4b	 1/1	 Running   0	      9m30s
nginx-56c45fd5ff-l676j	 1/1	 Running   0	      9m30s
?2004hroot@k8-0:[2026-02-14 05:07:27]-#BmAdded alias helpers
Added: command not found
?2004hroot@k8-0:[2026-02-14 05:12:45]-#Bm1@#1@#1@ias helpers
?2004hroot@k8-0:[2026-02-14 05:12:52]-#Bm## Let's jpKoin the other two domains
?2004hroot@k8-0:[2026-02-14 05:13:54]-#Bm7mkubeadm token create --print-join-command27m
ACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCkubeadm token create --print-join-command
A
kubeadm join 144.126.131.105:6443 --token yf2hc9.kxh53qrw6t1lk66d --discovery-token-ca-cert-hash sha256:cb7913639f6c172f24bc78a3e22e0d6814f690001b887adf438f23be20f06be7
?2004hroot@k8-0:[2026-02-14 05:14:01]-#Bmexit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-13 20:14:50]-$Bm9Psshnroot@k8-1.v-site.netig.yaml
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Sat Feb 14 05:14:59 CET 2026

  System load:		 0.07
  Usage of /:		 1.5% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 128
  Users logged in:	 0
  IPv4 address for eth0: 207.244.225.169
  IPv6 address for eth0: 2605:a140:2114:6819::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 04:32:43 2026 from 73.222.150.26
?2004h0;root@k8-1: ~root@k8-1:~# 7mjoin 144.126.131.105:6443 --token yf2hc9.kxh53qrw6t1lk66d --discovery-token-ca-cert-hash sha256:cb7913639f6c172f24bc78a3e22e0d6814f690001b887adf27m7m427m7m38f23be20f06be72join 144.126.131.105:6443 --token yf2hc9.kxh53qrw6t1lk66d --discovery-token-ca-cert-hash sha256:cb7913639f6c172f24bc78a3e22e0d6814f690001b887adf438f23be20f06be7
join:lunrecognized option '--token'
Try 'join --help' for more information.
?2004h0;root@k8-1: ~root@k8-1:~# pwd
/rootl
?2004h0;root@k8-1: ~root@k8-1:~# ls
CCCCCCCCCCCCCCCCCCCCCCChttps://github.com/l0r3zz/k8-tools.gitom/l0r3zz/k8-tools.git27m
Cloning into 'k8-tools'...
remote: Enumerating objects: 15, done.K
remote: Counting objects: 100% (15/15), done.K
remote: Compressing objects: 100% (11/11), done.K
remote: Total 15 (delta 3), reused 10 (delta 3), pack-reused 0 (from 0)K
Receiving objects: 100% (15/15), done.
Resolving deltas: 100% (3/3), done.
?2004h0;root@k8-1: ~root@k8-1:~# source k8-tools/k8.sh
?2004hroot@k8-1:[2026-02-14 05:16:17]-#Bm7mkubeadm join 144.126.131.105:6443 --token yf2hc9.kxh53qrw6t1lk66d --discovery-token-ca-cert-hash sha256:cb7913639f6c172f24bc27m7m727m7m8a3e22e0d6814f690001b887adf438f23be2kubeadm2join 144.126.131.105:6443 --token yf2hc9.kxh53qrw6t1lk66d --discovery-token-ca-cert-hash sha256:cb7913639f6c172f24bc78a3e22e0d6814f690001b887adf438f23be20f06be7
[preflight] Running pre-flight checks
	[WARNING ContainerRuntimeVersion]: You must update your container runtime to a version that supports the CRI method RuntimeConfig. Falling back to using cgroupDriver from kubelet config will be removed in 1.36. For more information, see https://git.k8s.io/enhancements/keps/sig-node/4033-group-driver-detection-over-cri
[preflight] Reading configuration from the "kubeadm-config" ConfigMap in namespace "kube-system"...
[preflight] Use 'kubeadm init phase upload-config kubeadm --config your-config-file' to re-upload it.
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/instance-config.yaml"
[patches] Applied patch of type "application/strategic-merge-patch+json" to target "kubeletconfiguration"
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
[kubelet-start] Starting the kubelet
[kubelet-check] Waiting for a healthy kubelet at http://127.0.0.1:10248/healthz. This can take up to 4m0s
[kubelet-check] The kubelet is healthy after 503.312226ms
[kubelet-start] Waiting for the kubelet to perform the TLS Bootstrap

This node has joined the cluster:
* Certificate signing request was sent to apiserver and a response was received.
* The Kubelet was informed of the new secure connection details.

Run 'kubectl get nodes' on the control-plane to see this node join the cluster.

?2004hroot@k8-1:[2026-02-14 05:16:45]-#Bmexit
logout
Connection to k8-1.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-13 20:17:14]-$Bm9Psshnroot@k8-2.v-site.netig.yaml
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Sat Feb 14 05:17:20 CET 2026

  System load:		 0.0
  Usage of /:		 1.5% of 192.69GB
  Memory usage:		 3%
  Swap usage:		 0%
  Processes:		 127
  Users logged in:	 0
  IPv4 address for eth0: 207.244.237.219
  IPv6 address for eth0: 2605:a140:2115:9519::1


Expanded Security Maintenance for Applications is not enabled.

1 update can be applied immediately.
1 of these updates is a standard security update.
To see these additional updates run: apt list --upgradable

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Fri Feb 13 04:32:04 2026 from 73.222.150.26
CCCCCCCCCCCCCgit2cloneohttps://github.com/l0r3zz/k8-tools.gitom/l0r3zz/k8-tools.git27m
Cloning into 'k8-tools'...
remote: Enumerating objects: 15, done.K
remote: Counting objects: 100% (15/15), done.K
remote: Compressing objects: 100% (11/11), done.K
remote: Total 15 (delta 3), reused 10 (delta 3), pack-reused 0 (from 0)K
Receiving objects: 100% (15/15), done.
Resolving deltas: 100% (3/3), done.
?2004h0;root@k8-2: ~root@k8-2:~# souKurce k8-tools/k8.sh
?2004hroot@k8-2:[2026-02-14 05:18:15]-#Bm7mkubeadm join 144.126.131.105:6443 --token yf2hc9.kxh53qrw6t1lk66d --discovery-token-ca-cert-hash sha256:cb7913639f6c172f24bc27m7m727m7m8a3e22e0d6814f690001b887adf438f23be2kubeadm2join 144.126.131.105:6443 --token yf2hc9.kxh53qrw6t1lk66d --discovery-token-ca-cert-hash sha256:cb7913639f6c172f24bc78a3e22e0d6814f690001b887adf438f23be20f06be7
[preflight] Running pre-flight checks
	[WARNING ContainerRuntimeVersion]: You must update your container runtime to a version that supports the CRI method RuntimeConfig. Falling back to using cgroupDriver from kubelet config will be removed in 1.36. For more information, see https://git.k8s.io/enhancements/keps/sig-node/4033-group-driver-detection-over-cri
[preflight] Reading configuration from the "kubeadm-config" ConfigMap in namespace "kube-system"...
[preflight] Use 'kubeadm init phase upload-config kubeadm --config your-config-file' to re-upload it.
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/instance-config.yaml"
[patches] Applied patch of type "application/strategic-merge-patch+json" to target "kubeletconfiguration"
[kubelet-start] Writing kubelet configuration to file "/var/lib/kubelet/config.yaml"
[kubelet-start] Writing kubelet environment file with flags to file "/var/lib/kubelet/kubeadm-flags.env"
[kubelet-start] Starting the kubelet
[kubelet-check] Waiting for a healthy kubelet at http://127.0.0.1:10248/healthz. This can take up to 4m0s
[kubelet-check] The kubelet is healthy after 503.184852ms
[kubelet-start] Waiting for the kubelet to perform the TLS Bootstrap

This node has joined the cluster:
* Certificate signing request was sent to apiserver and a response was received.
* The Kubelet was informed of the new secure connection details.

Run 'kubectl get nodes' on the control-plane to see this node join the cluster.

?2004hroot@k8-2:[2026-02-14 05:18:43]-#BmexioKexit
logout
Connection to k8-2.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-13 20:19:18]-$BmKls .kKpwd
/home/l0r3zz/.ssh
?2004hl0r3zz@tarnover:[2026-02-13 20:19:30]-$Bmcd ..
?2004hl0r3zz@tarnover:[2026-02-13 20:19:34]-$Bmls -l .kube
totall36
drwxr-xr-x 4 l0r3zz l0r3zz  4096 Jul 19	 2021 0m01;34mcache0m
-rw-rw-r-- 1 l0r3zz l0r3zz  5667 Mar 24	 2024 config
-rw------- 1 l0r3zz l0r3zz  5666 Feb 15	 2023 config.old
drwxr-xr-x 3 l0r3zz l0r3zz 12288 Feb 15	 2023 01;34mhttp-cache0m
drwxr-xr-x 3 l0r3zz l0r3zz  4096 Apr  9	 2017 01;34mschema0m
?2004hl0r3zz@tarnover:[2026-02-13 20:19:40]-$Bmcd .k\
?2004h> ub
bash:lcd: .kub: No such file or directory
?2004hl0r3zz@tarnover:[2026-02-13 20:19:53]-$Bmcd .kubeK
?2004hl0r3zz@tarnover:[2026-02-13 20:19:59]-$Bmrm config.old
?2004hl0r3zz@tarnover:[2026-02-13 20:20:06]-$Bmmv config configK.old
?2004hl0r3zz@tarnover:[2026-02-13 20:20:12]-$Bmless config.old
apiVersion:0v11h
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUMvakNDQWVhZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKY201bGRHVnpNQjRYRFRJek1ESXhOVEF6TlRJME9Wb1hEVE16TURJeE1qQXpOVEkwT1Zvd0ZURVRNQkVHQTFVRQpBeE1LYTNWaVpYSnVaWFJsY3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBS2o2CnF4ZGoxblRkeGVSM0UwMGt5U2hFOWFZSVhFeDFNVmxQYlFuTTYwZ2F0Z3ZmZFBTcU53aklKUmtnM2ZrbXErSG8KMTEwcVJGS0JManAxTGovdURLbnY4ZzdjVGd2ekZjR3VqV2pPK1NEVENZbmtNK3dDeUlHTGF2VlByQWJQOXFSSQpFQTlxcnY0WDFTWkVybDJxNXJWN3ZMVTgxb0R2ejFOS29oT1kvRDRmQ2drYjc4V28zQzZORVkxUWlyUW5OWlpnCnFGTE9sVVlSRWpkcUkzaXBmUDlVUnIvNmRDNzAvb2JVZ0U0cExVVFBYTERMWFZRejkyUVJPampKL2crZTRabXcKYm9GN3Z4SWxhUDkwTHNaTnRjbUNFcWxiNlpyVlQwTDlBejQxSFg1ZU5HNTdhbGFRRmJNeWp5b1R3MUlZSWE4cwpTOStMVXVnbGVNL3l6SXl0dURzQ0F3RUFBYU5aTUZjd0RnWURWUjBQQVFIL0JBUURBZ0trTUE4R0ExVWRFd0VCCi93UUZNQU1CQWY4d0hRWURWUjBPQkJZRUZLd0VJU2M3b1hneWRERUp5cy81dURvb0d1SnlNQlVHQTFVZEVRUU8KTUF5Q0NtdDFZbVZ5Ym1WMFpYTXdEUVlKS29aSWh2Y05BUUVMQlFBRGdnRUJBR0hiNnBwT2QzZG5teFRoMkYwdApmWG5HQzN4Y21pRVlFcitQTEFyRVVzWS9FYzEwL3U4MmYyTDBxcGtkcFBMdjQwTkVSMVM1NndEWklFM08xUEUwCkNleE1iV0RUUnYvTTROZ2dyQXpjbVJMaUhlNm1SSTBRb3pMaUJHSUdvS1R4cGZOVndxWjhLK1hHQzR1Y2YyTVYKUytPVlJCTmRBWjRKWmI5ZWdkbFFGOUNSeWhOMEdWVU8zYllGTnpxa21WUkJJTjRSL20xOFBjMTRDMGovNVI2ZwpXU0Jac2ZrdkhlQkZjdE1EYkxVUjZwenNKbUZ1T3pNU1JZNnpab1ExRktGSG4wYTJRWnI3bC8rSkNpdXp3WlM4CnhCeDFvY2Y5RnhPRUdUQlFnTjgvN3NxdVFSaG1ieW05Ny83RzVDREtxZHo4WmFub3oyb3BWTkxnMi9qaW5LdkUKc0FFPQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==
    server: https://144.126.131.105:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    namespace: kube-system
    user: kubernetes-admin
  name: kubernetes-admin@kubernetes
current-context: kubernetes-admin@kubernetes
kind: Config
preferences: {}
users:
- name: kubernetes-admin
  user:
    client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURJVENDQWdtZ0F3SUJBZ0lJRk85ZjQzd2NPQmN3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TXpBeU1UVXdNelV5TkRsYUZ3MHlOVEF5TURJeU1EVXhOVGRhTURReApGekFWQmdOVkJBb1REbk41YzNSbGJUcHRZWE4wWlhKek1Sa3dGd1lEVlFRREV4QnJkV0psY201bGRHVnpMV0ZrCmJXbHVNSUlCSWpBTkJna3Foa2lHOXcwQkFRRUZBQU9DQVE4QU1JSUJDZ0tDQVFFQXFVRUdMT0RIQ25wYldEa2MKVW5PeWtVNnJycGQ3YTZvTTlKeTFoVGhCd2tHZ0lwcHRGR0tTOWpCbmpkZzZKYUxKSXJmSUZaNkd2Ymk1ekJmVwp3MHFGOENGNTVTY2ZFcFV0Z1RuRzZsWWlSUDlydlFOMlh3b0o2bUZpRTh0ZXlrSVlZZnI1Slk5NDM1UlVCNEw2CnJ2OHB0K3dkVDBYNjFVcXFhbUU4QUxtSUUvb09jenNTRVVtSDQ1RlM5VGxzZ2JQQlkzdEh4SUpFQjdjbkRPZTAKNVdWZExoVEVDbW9taFR1V08vSkJudDFIemxtSnFMTG9sUzZvM2llQ1J3L3lZSTNEa002ZmFiMHJNa2NsS1NWagp0TysxSnpoRkdDMjVMYkthaFVQZ256aVlIQm9CendOMCtFbHlzeUE0Sy9ITEg4K3pjSEsvVitLTkp5WXdrUkNGClBFL2J2UUlEQVFBQm8xWXdWREFPQmdOVkhROEJBZjhFQkFNQ0JhQXdFd1lEVlIwbEJBd3dDZ1lJS3dZQkJRVUgKQXdJd0RBWURWUjBUQVFIL0JBSXdBREFmQmdOVkhTTUVHREFXZ0JTc0JDRW5PNkY0TW5ReENjclArYmc2S0JyaQpjakFOQmdrcWhraUc5dzBCQVFzRkFBT0NBUUVBbEE3RE12ajN5MXY0Y1JFemhqZlFhSHVDaytzSFhUaGZ3ekFCCkpQb0piVG1lWGprbGJwWUxzU3RVWFFmazhFeC9IUlduUHlqb0tXL0pjUUFoN0gxMEJMTUVVV1hPSExXSWt1L0wKemo5WHBpdzYyc0hUVlJnQ2FDeTRpOGNsUUhHVEFqcytiRUx5WDBvWXFYTlJmOGNSZHhBYVI2QndBRkJFVzNERwpESkFUSnYvODBEL2w4eVF3MkR4MDRSRTlpbk1QRzNVM1Q4bmNjZ2djVHZCNHN4RHhHL2U0OW9oSG5FaEtpdFBOCm0xY3JXc3dLOGFWK0NIRXQ4SnNUVk8rZDdUUEsxRE1uS1R6L0tGWWpaRURBNW1qSkNodmZ4bWVCbkxGc042VncKdFUyeWFPM3V6Q2RHaUF2VGpYWFkzd2tLRkhVRHhpNGpyUS94TzVaUmZWRFFTa25PNXc9PQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==
KwTlB6T3h2QldnMEh4bllHUGErSEFRWTl2WDM3ekZEZ01CdmpZQ3p1TmRzUk1oV1FoSjdpaUIvQ2Q5OTJHK0x6Cml5YU5Bb0dBVVFnNVhWb0V3bUFoL2NHd1dReWJaZHNTbElsdlFxbFJWNE4rN2FDemIwWVRSY0RBQ2lmZWJiYjUKRER6d1IvN2hyL04vZEdVcm0rd2NRWmFCVnh2UE52dElQMUNveGw0QnYzdGZ6amxGQTYwZWI5S1pQL284MVNKVgp3VVg2UU1YNlV3NTUzMmEyclpGUkdLMk16MWhvSXBTNXZuNUlUTkJBSHJWUDdLTGQraDQ9Ci0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0tCg==FRFQ21vbWhUdVdPL0pCbnQxSHpsbUpxTExvCmxTNm8zaWVDUncveVlJM0RrTTZmYWIwck1rY2xLU1ZqdE8rMUp6aEZHQzI1TGJLYWhVUGduemlZSEJvQnp3TjAKK0VseXN5QTRLL0hMSDgremNISy9WK0tOSnlZd2tSQ0ZQRS9idlFJREFRQUJBb0lCQUExZURWYk9DZXBSNzVUdwpMY1IxVHMwYklZUVFncmJtSDAvU2NLT3M1Y1NwMmpQaGJtd0Z2UVdrblFrZTRyakdPb3g3WjFvTnd5YUl5R1BPCkhqQWVXcVcwZnlRU0N1bzB6ZnMrek84RkRuL1VqSFhKS0RncFdzOGdFZGJ1WVBZb2NqU0sxZEtabWpwT1JMU3oKSzRsV3JielE4UitwcnozWlA4eFhFWjRkQ1JwS3JLWXVwZVVhSHBHTDVUbm9UMW4wUHNIRjNnbUdXbGRnZFNYbgpNcXFJZExjV3NGR0hDOENsSlNWY3dSRmNFQzVwU3JObWJreUg3Rmd4YzJBWWhBdG95a1EvVVdXKzhBcENqRzZJCmRiRlIxcWR5a2s0MnpxQ05IYWpBRUxtQU94L0ZIbExkdTk3V1V5RFd3YlFTYlNIL3JGdm00dUxHcnE1OTRNcFoKK1pkN2RnRUNnWUVBeTY0L3hNcjk0SDJQNHZ0Z3Q4NVE0U1JxMnR3VWR0OVVsSVdvQlJVQnZ4YldWbXFXMUdlWQo1Q010TXVrWjcvQnFsVG0rbE04ZjhRQlJCRUFUV3MxRUFRNno5L3A5VXo2dU5kVjlaQjRMQyt2d2o2ZC9KQkQ0CmVRWUdOVVZBTnFFUEV3SEVsUHp5NmNLTUV0SUF4L25LbFlSMmVpMk5rVllvTzg4R0JXS29PdkVDZ1lFQTFMcnQKUUcxM1pGazQ1R21NUjJJWWRGTnBFTDhQMWZtT3FmUTlTTnFGcnJ0SGp0bWdCSlJLOXpja2ZmeTY5VGpkZlgvcApqMStxa2VCU0tVYmtwYUFiTDNieWFYV1FSa2p2UVpLNHphV09aK0hNTEJwZTBCbGdadGhoTlBmTDFqUTBrcHhnCmtjN3FCZ042VFN5aGJDMnlHMTczTDdlQ2FmUDdPTTFnOU9XcnRZMENnWUFndnBxeDRKQ0FEcStiSmg2ZWJpVEMKalVCQWZ6RXJDeXhsMURiMjJqRzFyczQyaGx4Sk9YNXk3dFROWW53dy9zMmp2K3pMcjZESzllb1FiTnl2dEdCQwphMEt6a3ltaXdHanhicWtCOTNKL01DYzBjUkVYazBMZThnRDlmMnliVzdrNHJRZ1ZpN1RocjgwbEdXM1d1R25CCkw5SjhRZWFJZnZsbzVCZHJ0amlsZ1FLQmdEckxRd0U0Zi9QekdOOUFNSzRWOVk1STgxUFdpb2pvQlQ4QnF1SjAKeXRmRkdQenBOdW10RnA4RzFZWWdrSWR2NVA5bmwrU3hXeElnUG5UOEMvdWVxWVRQeWlYTmdVZDdwdXlub1gzcwo7mconfig.old27mK

KHm(ENcertificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSUMvakNDQWVhZ0F3SUJBZ0lCQURBTkJna3Foa2lHOXcwQkFRc0ZBREFWTVJNd0VRWURWUVFERXdwcmRXSmwKYH- cluster:
Hclusters:
HapiVersion: v1
K?1l?1049l23;0;0t?2004hl0r3zz@tarnover:[2026-02-13 20:20:43]-$Bm6P6Pc6P2Psshkroot@k8-0.v-site.net
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Sat Feb 14 05:20:58 CET 2026

  System load:		 2.14
  Usage of /:		 2.8% of 192.69GB
  Memory usage:		 14%
  Swap usage:		 0%
  Processes:		 173
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Sat Feb 14 04:26:33 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# ls
admin.conf  0m01;34mk8-tools0m	kubeadm-config.yaml  01;34msnap0m
?2004h0;root@k8-0: ~root@k8-0:~# ls .kube/
0m01;34mcache0m	 config
?2004h0;root@k8-0: ~root@k8-0:~# cat .kube/config
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWUyZ0F3SUJBZ0lJUXE4Q2dwMlNJQkF3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TmpBeU1UUXdNekl5TkRSYUZ3MHpOakF5TVRJd016STNORFJhTUJVeApFekFSQmdOVkJBTVRDbXQxWW1WeWJtVjBaWE13Z2dFaU1BMEdDU3FHU0liM0RRRUJBUVVBQTRJQkR3QXdnZ0VLCkFvSUJBUUM0WUg0citGZ1RvNVQwRWVkWTBUSnpmNFZneHNGQzJLUWdyb01oVkpMNXk2TE1UdC9TTDlKYXZQSmcKc0dpRUdMazNLQnhxV2JPVjluelJsOFhMUkRFOWIwNHhPd3FlWWNaaW0vcjRpQUwrT0Jkb2JrZ1VCZW9KeXdOcApwTEpnWStjRklrSkRrWit3ZkhTV0M3MEZnQkRYM1NKRFhIWktHSjFaVVJrY0N1dy9oUkVYeE1Fd1ZWU0VPdEQzCmc3T29jQUxZWGx6ckVMelpLR2hQU2oyRml0cDJTMU9Sa1ppb0JhdnRVb3lnZlh5OGEvQnNhSWIveUtQUGlaNVoKUFB0SjAxNXN4amswSmNHK0hLRmVUSmVPd0I1T0EwZ3JSd0pyUllqNHZqK0N3d1lmQ2ZFY2JHR0t5dExwR0w0SQpZR0h2SzU0YVR1UzhYeVM2VnZpUnF1LzFHTGZmQWdNQkFBR2pXVEJYTUE0R0ExVWREd0VCL3dRRUF3SUNwREFQCkJnTlZIUk1CQWY4RUJUQURBUUgvTUIwR0ExVWREZ1FXQkJTeDFnSjhudjVQM0FIbWJtbWQxd3lDTGh5dEtqQVYKQmdOVkhSRUVEakFNZ2dwcmRXSmxjbTVsZEdWek1BMEdDU3FHU0liM0RRRUJDd1VBQTRJQkFRQ1BkVm1BVW5aSApGNkFGQm5TY1BOTkJuWVpjUjAwbWgrQlBjck85dlgwZGhhR1RNVHBWQW1jazB1VENYazE5blBDWTloL1pVZkxOCjduRjdVN0I4OSs1M1JMb0ZQT3AyVDFNM1AyYkJ3MDhxSnB6V0QxSnkvU2JVenNjR0NTTjlGZjZXaU1ubmJtTTkKRlFmL3lFL3hKZUpKbWNUUGlnWDNDSUozaHdabmx5K25tdTZiRjdQLzczdEhKSW9RMGlIdFRBN25tRndXb2F0Zgo5RVV1OHE4S2ZFZndPeGhmM0hmOHNMdStTMGszQ0JEazlyV2E3cDhlakQxVEYxU2RhUmZyZ3lKK1Y2UWNQRjB1CkhwNllla3NWd0tEV2NDTmlmTVlGYytjZHV4Y2JlWVh0Si9qS2s0WU1BRXVWVDJwN1ZwTEdqRGxucHM1cVc0dnEKcWExSVMzOWg4cXU5Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K
    server: https://144.126.131.105:6443
  name: v-site-cluster
contexts:
- context:
    cluster: v-site-cluster
    user: kubernetes-admin
  name: kubernetes-admin@v-site-cluster
current-context: kubernetes-admin@v-site-cluster
kind: Config
users:
- name: kubernetes-admin
  user:
    client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURLVENDQWhHZ0F3SUJBZ0lJVzdYTGlTRDZVcmN3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TmpBeU1UUXdNekl5TkRSYUZ3MHlOekF5TVRRd016STNORFJhTUR3eApIekFkQmdOVkJBb1RGbXQxWW1WaFpHMDZZMngxYzNSbGNpMWhaRzFwYm5NeEdUQVhCZ05WQkFNVEVHdDFZbVZ5CmJtVjBaWE10WVdSdGFXNHdnZ0VpTUEwR0NTcUdTSWIzRFFFQkFRVUFBNElCRHdBd2dnRUtBb0lCQVFEN285a1kKMzlmZWk1aXFNaEtkdWJTSUZwRXF3Tlg0OHhtd2dwaWdEL2R1b2lNZVpFWEZ4UWZRcEc1SU9PMHFENzFtZnRyLwpPZTh0anJIL05Mclg4NUg2RXF1UU5wNW4rV0x2T0VtUEtPRXdKUmZzdXNwNDIxL2RLZDJpVzYzTk9XNDBxbEZlCmxIZlJkcFFrYkk5VzQzSkFJb3VvaTZnUXk1OTRVbVEyZTVFR1BuMXZjV0thc1ZBNkZFMHpLbTQ4RTFvd1RrS1oKZXgzTEZMZFFvY2V0bGc3SzZPWTc2YytUNzA0Q0Y1TmZhQ2hSMXFuMCt4M1lodm5zR0k5d3Y0Z3duUTgxaE1FeQp5SjVETU5yV2hqN0dCNTBCS0ZBajYxQzJteXZZQ3d5MVlxY0EvUnJEcnFLcWUzeU1hcjJwV25lOVhvRk1uVUdsCjJBSVVkQjZSUVU4WWRsenZBZ01CQUFHalZqQlVNQTRHQTFVZER3RUIvd1FFQXdJRm9EQVRCZ05WSFNVRUREQUsKQmdnckJnRUZCUWNEQWpBTUJnTlZIUk1CQWY4RUFqQUFNQjhHQTFVZEl3UVlNQmFBRkxIV0FueWUvay9jQWVadQphWjNYRElJdUhLMHFNQTBHQ1NxR1NJYjNEUUVCQ3dVQUE0SUJBUUFkNndFcnhiMGVtd2VJVjUybkFmRVZoVUFMCmErR0VlRTVMRE9JOUVSZ2VqdElOb2J2anFGR09GaG5vRVc4dFQzT2NSakFoUlRqTC9OWk5xMjNSSDA3OWRvQ2EKbHh5YVMxOXFPR2k5N0VPVUNCSGgvVmpjWlFJdTRMRVBuVFYwYzZ6RTM4UnYrZGZoblpTMXB4M25MZHZtTHdLMAo2Rm9LRXFjeU5IU1ZnSXd6bmorS24wbEJrRXJWWmFPMkRXUTFPSDJ2TE1pN0J0WDF0TmlydnMyRFNUTjVKOWFnCld0WUV4TXBRanFIa1YyL3N6VDBZYms3d2d0cGNNTEZpL0RXMFFmRC9JU1AvY3F5YThNbHQxQVhWYklzZ0Y5am4KRUYwamJGOElIM25JVE56b3NqRzdVTXNhT2xPeHBaYXNOeEMxOXZDN2NnL3dDc0hOMGpsWlpqcjByZC9aCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K
    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFcEFJQkFBS0NBUUVBKzZQWkdOL1gzb3VZcWpJU25ibTBpQmFSS3NEVitQTVpzSUtZb0EvM2JxSWpIbVJGCnhjVUgwS1J1U0RqdEtnKzlabjdhL3pudkxZNngvelM2MS9PUitoS3JrRGFlWi9saTd6aEpqeWpoTUNVWDdMcksKZU50ZjNTbmRvbHV0elRsdU5LcFJYcFIzMFhhVUpHeVBWdU55UUNLTHFJdW9FTXVmZUZKa05udVJCajU5YjNGaQptckZRT2hSTk15cHVQQk5hTUU1Q21Yc2R5eFMzVUtISHJaWU95dWptTytuUGsrOU9BaGVUWDJnb1VkYXA5UHNkCjJJYjU3QmlQY0wrSU1KMFBOWVRCTXNpZVF6RGExb1kreGdlZEFTaFFJK3RRdHBzcjJBc010V0tuQVAwYXc2NmkKcW50OGpHcTlxVnAzdlY2QlRKMUJwZGdDRkhRZWtVRlBHSFpjN3dJREFRQUJBb0lCQUdickdIdW44VzQvd2V5NgpGZ3NVVE5Yc0JPdHJleGdhdFVNUDVzUndRMDZvV1p5d2Zpam84TTFRc3hvdXpqRUp4dmtJb1NFSjNOelJJOU94CkNVb1JnSDY2N0JoTGZuWWY5V3JKcHF3NmwvOU03SUFSMVlXZ2s1Q3M4c3pZbWpqNWFDMTZDMVdYZTNuYitiTDgKQTVRUjZrUjQzSTNPc0twTjNhY2thNEF0QVo5L1Y4aVcycWFLVHAvY3dKb0pyYWQ4UmJsQ3JZT1dXaFZ2em9TNgpvNkVjOEVlUEV1V0h4Z2E0L1NiQUVVM0JuWHU4eHBLL2c0TzR0TnJPclE1RUowZEsxYXlmclhBRmxOSWt4dHdOCmJEMjRyaHRpdUlwUGVXd1JrYkJSUWRtSDh2Zk1hWjN6ME9IT0UzYWtuN1p0b2UwMG4xK0tFTUtiN01rWCt5MDIKUW95ZEVRRUNnWUVBL2NNYVBpU2lHWVZuRlZsUFh1Tnp5ZXI5bTJBcTRIcjFDeldhWnFZZnV2dHZuZGY4YjN6eApTTWpOM0pXRk9FZm56UWRuUUZYZ3FRYnFNdmFNdDVOeHYvZHpkQkVLNmV5dldYZm03UWVKMVBrQUs3WlZZbW1nCmRHRGJrTmNmWWIrVFNnQmNLMWgzM1BSUHU2WURyMlAyNzd6WlYvaVpMZlJzK3ZJTEtnZmV2MDhDZ1lFQS9kdjAKWk85WWVmWUNtUmIvVVZtc3NhVlE1T2FIUEhsNjAxK1h0UjNybVJzOHEwRXN6QWRERGcwZEJBU25SWHlQTjlzNApXTXl2ZXJHNXplNlhubGdBU0kvaTA1SnBhNFp2aWswZlg3SkxzdFFUN3ZqTVZiaWxVTXVmN3Z4MjROd2FydHFtCmtBVzdjZ0xFcFdFVHNiNTNUWVVoaTg0T001K2Vrd0xldk83NklHRUNnWUVBelE4L0FwNlp1eVBaQkNCeWlnd2wKUWpLNWt6Z29EZFJ1ZGd0djVLa3psT2FmOEo1YnFELy92c0E5MHBXazNMRUdlT0VWcDZCOTlqalhRaTJIMHNTOApNOU1qb2RRdnpJNXR1RSt5OVRHVlNOdWFMcmlkMFBQb0xJTWtpcXU3K1VKVkpJU2I5bzc3OVRvYndGaE1QQXY4CnZRZ1BYZzVPd2hyMWdlZmI2N0FHYVBNQ2dZRUE5d3V3NFBGVDV3eVVKcXVNdUh4T1pXcitPR1JudzJCdE9YclQKeG54aHBOUXV6SEpXeUE5aElERit4VVJLRElOVlZRUlA1NHI2VXFyV3FTUENCV1Nha2dNRXVPVEpGc3p6aTJIVwpZR2pBNWowaFVQUnExaGtsT0dXUk5TQVlDR2ZxeDdNZFdSZGEvVzdZTkNFdTYxRHlCVXpFQXF2NmdoNmFVWEwvCmxGbjByTUVDZ1lCUVVEdzNPdHAzTzl6alF5VFBqVzNkMzU5NFovTjNHWGFKazFJMmRzeXM4cUc3Qk1kY0VabXoKaXFzcktxK1J2MytVZWh0QkFvSXlyRGkwWWF1eU5CRmxVMmtvbk91cy9HVmJtQXB0bXNhN1A4aXdsMkNBMkk1bwo2QTZPSkhrM3ppOVd3NFYxVzRSaU95clBmTHhZLzlpR1kvN2x1dSs4WGhyaHBPYXZwVWthNkE9PQotLS0tLUVORCBSU0EgUFJJVkFURSBLRVktLS0tLQo=
?2004h?2004l@k8-0: ~root@k8-0:~# ^C?2004l
?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-13 20:21:55]-$Bmvi .kuKvi .kubeKpwd
/home/l0r3zz/.kube
?2004hl0r3zz@tarnover:[2026-02-13 20:22:16]-$BmvKls
0m01;34mcache0m	 config.old  01;34mhttp-cache0m	 01;34mschema0m
?2004hl0r3zz@tarnover:[2026-02-13 20:22:20]-$Bmvi config
?1000h?1049h22;0;0t>4;2m?1h?2004h?1004h1;50r?12h?12l22;2t22;1t27m23m29mm38;5;244m48;5;234mH2J?25l50;1H"config" [New]2;1H▽6n2;1H	 3;1Hzz0%m6n3;1H	   1;1H>c10;?11;?1;1H38;5;17m48;5;190m config m38;5;244m48;5;234m38;5;190m48;5;234m m38;5;244m48;5;234m38;5;85m48;5;234m																	 m38;5;244m48;5;234m38;5;234m48;5;234m<m38;5;244m48;5;234m38;5;214m48;5;234m<m38;5;244m48;5;234m38;5;232m48;5;214m buffers m38;5;244m48;5;234m2;1H38;5;239m48;5;235m  1 m38;5;244m48;5;234m2;5HK3;1H1m38;5;240m~																			    4;1H~																			     5;1H~																			      6;1H~																			       7;1H~																				8;1H~																				 9;1H~																				  10;1H~																			    11;1H~																			      12;1H~																				13;1H~																				  14;1H~																			    15;1H~																			      16;1H~																				17;1H~																				  18;1H~																			    19;1H~																			      20;1H~																				21;1H~																				  22;1H~																			    23;1H~																			      24;1H~																				25;1H~																				  26;1H~																			    27;1H~																			      28;1H~																				29;1H~																				  30;1H~																			    31;1H~																			      32;1H~																				33;1H~																				  34;1H~																			    35;1H~																			      36;1H~																				37;1H~																				  38;1H~																			    39;1H~																			      40;1H~																				41;1H~																				  42;1H~																			    43;1H~																			      44;1H~																				45;1H~																				  46;1H~																			    47;1H~																			      48;1H~																				m38;5;244m48;5;234m49;1H38;5;17m48;5;190m m38;5;244m48;5;234m1m38;5;17m48;5;190mNORMALm38;5;244m48;5;234m38;5;17m48;5;190m m38;5;244m48;5;234m38;5;190m48;5;238m>m38;5;244m48;5;234m38;5;238m48;5;234m>m38;5;244m48;5;234m38;5;85m48;5;234m config													      m38;5;244m48;5;234m38;5;234m48;5;234m<m38;5;244m48;5;234m38;5;238m48;5;234m<m38;5;244m48;5;234m38;5;255m48;5;238m [unix] m38;5;244m48;5;234m38;5;190m48;5;238m<m38;5;244m48;5;234m38;5;17m48;5;190m 100% m38;5;244m48;5;234m1m38;5;17m48;5;190m:	 0/1m38;5;244m48;5;234m38;5;17m48;5;190m :  1 m38;5;244m48;5;234m38;5;166m48;5;190m<m38;5;244m48;5;234m38;5;160m48;5;166m<2;5H?25h+q436f+q6b75+q6b64+q6b72+q6b6c+q2332+q2334+q2569+q2a37+q6b31?1000l?1006h?1002h?1006l?1002l?1006h?1002h$q q?12$p?25lm38;5;244m48;5;234m50;147H02;5H50;148H02;5H50;149H02;5H50;150H/2;5H50;151H02;5H50;152H02;5H50;153H02;5H50;154H02;5H50;155H/2;5H50;156H02;5H?25h?25l50;147H		 2;5H?25h?25l50;147Hi2;5H50;147H 2;5H50;1H38;5;33m-- INSERT --m38;5;244m48;5;234m50;13HK49;1H38;5;17m48;5;45m m38;5;244m48;5;234m1m38;5;17m48;5;45mINSERTm38;5;244m48;5;234m38;5;17m48;5;190m m38;5;244m48;5;23438;5;17m48;5;45m m38;5;244m48;5;234m38;5;45m48;5;27m>m38;5;244m48;5;234m38;5;27m48;5;17m>m38;5;244m48;5;234m97m48;5;17m config														  m38;5;244m48;5;234m38;5;17m48;5;17m<m38;5;244m48;5;234m38;5;27m48;5;17m<m38;5;244m48;5;234m38;5;255m48;5;27m [unix] m38;5;244m48;5;234m38;5;45m48;5;27m<m38;5;244m48;5;234m38;5;17m48;5;45m 100% m38;5;244m48;5;234m1m38;5;17m48;5;45m:m38;5;244m48;5;234m1m38;5;17m48;5;190m m38;5;244m48;5;2341m38;5;17m48;5;45m   0m38;5;244m48;5;234m1m38;5;17m48;5;190m/m38;5;244m48;5;2341m38;5;17m48;5;45m/1m38;5;244m48;5;234m38;5;17m48;5;190m m38;5;244m48;5;23438;5;17m48;5;45m :	1 m38;5;244m48;5;234m38;5;166m48;5;45m<2;5H?25h?25l?25hm38;5;244m48;5;234m1;1H38;5;17m48;5;45m config+ m38;5;244m48;5;234m38;5;45m48;5;234m ?25lm38;5;244m48;5;234m2;5HapiVersion: v1
38;5;239m48;5;235m  2 m38;5;244m48;5;234mclusters:3;14HK4;1H38;5;239m48;5;235m	3 m38;5;244m48;5;234m- cluster:4;15HK5;1H38;5;239m48;5;235m  4 m38;5;244m48;5;234m    certificate-auth5;25HK49;1H38;5;17m48;5;172m m38;5;244m48;5;234m1m38;5;17m48;5;172mINSERTm38;5;244m48;5;234m38;5;17m48;5;45m m38;5;244m48;5;23438;5;17m48;5;172m > PASTE m38;5;244m48;5;234m38;5;172m48;5;27m>m38;5;244m48;5;234m38;5;27m48;5;53m>m38;5;244m48;5;234m38;5;255m48;5;53m config[+]												       m38;5;244m48;5;234m38;5;17m48;5;53m<m38;5;244m48;5;234m20C1m38;5;17m48;5;45m4/4m38;5;244m48;5;234m38;5;17m48;5;45m 5;25H?25h?25lm38;5;244m48;5;234mority-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWU?25h?25lyZ0F3SUJBZ0lJUXE4Q2dwMlNJQkF3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTU?25h?25lJFR0ExVV6;1H38;5;239m48;5;235m	  m38;5;244m48;5;234mUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TmpBeU1UUXdNekl5TkRSY6;61HK6;61H?25h?25lUZ3MHpOakF5TVRJd016STNORFJhTUJVeApFekFSQmdOVkJBTVRDbXQxWW1WeWJt?25h?25lVjBaWE13Z2dFaU1BMEdDU3FHU0liM0RRRUU7;1H38;5;239m48;5;235m    m38;5;244m48;5;234mJBUVVBQTRJQkR3QXdnZ0VLCkFvSUJ7;34HK7;34H?25h?25lBUUM0WUg0citGZ1RvNVQwRWVkWTBUSnpmNFZneHNGQzJLUWdyb01oVkpMNXk2TE?25h?25l1UdC9TTDlKYXZQSmcKc0dpRUdMazNLQnhxV2JPVjluelJsOFhMUkRFOWIwNHhh8;1H38;5;239m48;5;235m    m38;5;244m48;5;234mPd8;7HK8;7H?25h?25l3FlWWNaaW0vcjRpQUwrT0Jkb2JrZ1VCZW9KeXdOcApwTEpnWStjRklrSkRrWit3?25h?25lZkhTV0M3MEZnQkRYM1NKRFhIWktHSjFaVVJrY0N1dy9oUkVYeE1Fd1ZWU0VPdEQ?25h?25lzCmc3T29jQUxZWGx6ckVMelpLL9;1H38;5;239m48;5;235m    m38;5;244m48;5;234mR2hQU2oyRml0cDJTMU9Sa1ppb0JhdnRVb3lnZl9;43HK9;43H?25h?25lh5OGEvQnNhSWIveUtQUGlaNVoKUFB0SjAxNXN4amswSmNHK0hLRmVUSmVPd0I1T?25h?25l0EwZ3JSd0pyUllqNHZqK0N3d1lmQ2ZFY2JHR0t5dExwR0w0SQpZRR10;1H38;5;239m48;5;235m	 m38;5;244m48;5;234m0h2SzU0YVR110;16HK10;16H?25h?25lUzhYeVM2VnZpUnF1LzFHTGZmQWdNQkFBR2pXVEJYTUE0R0ExVWREd0VCL3dRRUF?25h?25l3SUNwREFQCkJnTlZIUk1CQWY4RUJUQURBUUgvTUIwR0ExVWREZ1FXQkJTeDFnSj?25h?25lhudjVQM0FIbWJtbWW11;1H38;5;239m48;5;235m    m38;5;244m48;5;234mQxd3lDTGh5dEtqQVYKQmdOVkhSRUVEakFNZ2dwcmRXSmxjb11;52HK11;52H?25h?25lTVsZEdWek1BMEdDU3FHU0liM0RRRUJDd1VBQTRJQkFRQ1BkVm1BVW5aSApGNkFG?25h?25lQm5TY1BOTkJuWVpjUjAwbWgrQlBjck85dlgwZGhhR1RR12;1H38;5;239m48;5;235m	   m38;5;244m48;5;234mNVHBWQW1jazB1VENYazE12;25HK12;25H?25h?25l5blBDWTloL1pVZkxOCjduRjdVN0I4OSs1M1JMb0ZQT3AyVDFNM1AyYkJ3MDhxSn?25h?25lB6V0QxSnkvU2JVenNjR0NTTjlGZjZXaU1ubmJtTTkKRlFmL3lFL3hKZUpKbWNUU?25h?25lGlnWDNDD13;1H38;5;239m48;5;235m	m38;5;244m48;5;234mSUozaHdabmx5K25tdTZiRjdQLzczdEhKSW9RMGlIdFRBN25tRndXb2F013;61HK13;61H?25h?25lZgo5RVV1OHE4S2ZFZndPeGhmM0hmOHNMdStTMGszQ0JEazlyV2E3cDhlakQxVEY?25h?25lxU2RhUmZyZ3lKK1Y2UWNQRjB1CkhwNlllaa14;1H38;5;239m48;5;235m    m38;5;244m48;5;234m3NWd0tEV2NDTmlmTVlGYytjZHV4Y214;34HK14;34H?25h?25lJlWVh0Si9qS2s0WU1BRXVWVDJwN1ZwTEdqRGxucHM1cVc0dnEKcWExSVMzOWg4c?25h?25lXU5Ci0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K
38;5;239m48;5;235m  5 m38;5;244m48;5;234m    server: https://14415;28HK15;28H?25h?25l.126.131.105:6443
38;5;239m48;5;235m  6 m38;5;244m48;5;234m  name: v-site-cluster16;27HK17;1H38;5;239m48;5;235m  7 m38;5;244m48;5;234mcontexts:17;14HK18;1H38;5;239m48;5;235m  8 m38;5;244m48;5;234m- context:18;15HK19;1H38;5;239m48;5;235m  9 m38;5;244m48;5;234m101m m38;5;244m48;5;234m19;6HK19;6H?25h?25l   cluster: v-site-cluster
38;5;239m48;5;235m 10 m38;5;244m48;5;234m    user: kubernetes-admin20;31HK21;1H38;5;239m48;5;235m 11 m38;5;244m48;5;234m  name: k21;14HK21;14H?25h?25lubernetes-admin@v-site-cluster
38;5;239m48;5;235m 12 m38;5;244m48;5;234mcurrent-context: kubernetes-admi22;37HK22;37H?25h?25ln@v-site-cluster
38;5;239m48;5;235m 13 m38;5;244m48;5;234mkind: Config23;17HK24;1H38;5;239m48;5;235m 14 m38;5;244m48;5;234musers:24;11HK25;1H38;5;239m48;5;235m 15 m38;5;244m48;5;234m- name: kubernetes-admin25;29HK26;1H38;5;239m48;5;235m 16 m38;5;244m48;5;234m101m m38;5;244m48;5;234m26;6HK26;6H?25h?25l user:
38;5;239m48;5;235m 17 m38;5;244m48;5;234m    client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0F27;61HK27;61H?25h?25lURS0tLS0tCk1JSURLVENDQWhHZ0F3SUJBZ0lJVzdYTGlTRDZVcmN3RFFZSktvWk?25h?25llodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKK28;1H38;5;239m48;5;235m	   m38;5;244m48;5;234mQXhNS2EzVmlaWEp1WlhSbGN6QWVGd28;34HK28;34H?25h?25lzB5TmpBeU1UUXdNekl5TkRSYUZ3MHlOekF5TVRRd016STNORFJhTUR3eApIekFk?25h?25lQmdOVkJBb1RGbXQxWW1WaFpHMDZZMngxYzNSbGNpMWhaRzFwYm5NeEdUQVhCZZ29;1H38;5;239m48;5;235m	m38;5;244m48;5;234m0529;7HK29;7H?25h?25lWQkFNVEVHdDFZbVZ5CmJtVjBaWE10WVdSdGFXNHdnZ0VpTUEwR0NTcUdTSWIzRF?25h?25lFFQkFRVUFBNElCRHdBd2dnRUtBb0lCQVFEN285a1kKMzlmZWk1aXFNaEtkdWJTS?25h?25lUZwRXF3Tlg0OHhtd2dwaWdEL2230;1H38;5;239m48;5;235m	   m38;5;244m48;5;234mR1b2lNZVpFWEZ4UWZRcEc1SU9PMHFENzFtZnRy30;43HK30;43H?25h?25lLwpPZTh0anJIL05Mclg4NUg2RXF1UU5wNW4rV0x2T0VtUEtPRXdKUmZzdXNwNDI?25h?25lxL2RLZDJpVzYzTk9XNDBxbEZlCmxIZlJkcFFrYkk5VzQzSkFJb3VV31;1H38;5;239m48;5;235m	m38;5;244m48;5;234mvaTZnUXk1OT31;16HK31;16H?25h?25lRVbVEyZTVFR1BuMXZjV0thc1ZBNkZFMHpLbTQ4RTFvd1RrS1oKZXgzTEZMZFFvY?25h?25l2V0bGc3SzZPWTc2YytUNzA0Q0Y1TmZhQ2hSMXFuMCt4M1lodm5zR0k5d3Y0Z3du?25h?25lUTgxaE1FeQp5SjVEE32;1H38;5;239m48;5;235m    m38;5;244m48;5;234mTU5yV2hqN0dCNTBCS0ZBajYxQzJteXZZQ3d5MVlxY0EvUnJ32;52HK32;52H?25h?25lEcnFLcWUzeU1hcjJwV25lOVhvRk1uVUdsCjJBSVVkQjZSUVU4WWRsenZBZ01CQU?25h?25lFHalZqQlVNQTRHQTFVZER3RUIvd1FFQXdJRm9EQVRCZZ33;1H38;5;239m48;5;235m	  m38;5;244m48;5;234m05WSFNVRUREQUsKQmdnc33;25HK33;25H?25h?25lkJnRUZCUWNEQWpBTUJnTlZIUk1CQWY4RUFqQUFNQjhHQTFVZEl3UVlNQmFBRkxI?25h?25lV0FueWUvay9jQWVadQphWjNYRElJdUhLMHFNQTBHQ1NxR1NJYjNEUUVCQ3dVQUE?25h?25l0SUJBUUU34;1H38;5;239m48;5;235m    m38;5;244m48;5;234mFkNndFcnhiMGVtd2VJVjUybkFmRVZoVUFMCmErR0VlRTVMRE9JOUVSZ234;61HK34;61H?25h?25lVqdElOb2J2anFGR09GaG5vRVc4dFQzT2NSakFoUlRqTC9OWk5xMjNSSDA3OWRvQ?25h?25l2EKbHh5YVMxOXFPR2k5N0VPVUNCSGgvVmpp35;1H38;5;239m48;5;235m    m38;5;244m48;5;234mjWlFJdTRMRVBuVFYwYzZ6RTM4UnYr35;34HK35;34H?25h?25lZGZoblpTMXB4M25MZHZtTHdLMAo2Rm9LRXFjeU5IU1ZnSXd6bmorS24wbEJrRXJ?25h?25lWWmFPMkRXUTFPSDJ2TE1pN0J0WDF0TmlydnMyRFNUTjVKOWFnCld0WUV4TXBRR36;1H38;5;239m48;5;235m	 m38;5;244m48;5;234man36;7HK36;7H?25h?25lFIa1YyL3N6VDBZYms3d2d0cGNNTEZpL0RXMFFmRC9JU1AvY3F5YThNbHQxQVhWY?25h?25lklzZ0Y5am4KRUYwamJGOElIM25JVE56b3NqRzdVTXNhT2xPeHBaYXNOeEMxOXZD?25h?25lN2NnL3dDc0hOMGpsWlpqcjByZZ37;1H38;5;239m48;5;235m    m38;5;244m48;5;234mC9aCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS037;43HK37;43H?25h?25lK
38;5;239m48;5;235m 18 m38;5;244m48;5;234m    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0t38;66HK38;66H?25h?25lLQpNSUlFcEFJQkFBS0NBUUVBKzZQWkdOL1gzb3VZcWpJU25ibTBpQmFSS3NEVit?25h?25lQTVpzSUtZb0EvM2JxSWpIbVJGCnhjj39;1H38;5;239m48;5;235m	   m38;5;244m48;5;234mVUgwS1J1U0RqdEtnKzlabjdhL3pudkxZNn39;39HK39;39H?25h?25lgvelM2MS9PUitoS3JrRGFlWi9saTd6aEpqeWpoTUNVWDdMcksKZU50ZjNTbmRvb?25h?25lHV0elRsdU5LcFJYcFIzMFhhVUpHeVBWdU55UUNLTHFJdW9FTXVmZUZKaa40;1H38;5;239m48;5;235m	m38;5;244m48;5;234m05udVJC40;12HK40;12H?25h?25lajU5YjNGaQptckZRT2hSTk15cHVQQk5hTUU1Q21Yc2R5eFMzVUtISHJaWU95dWp?25h?25ltTytuUGsrOU9BaGVUWDJnb1VkYXA5UHNkCjJJYjU3QmlQY0wrSU1KMFBOWVRCTX?25h?25lNpZVF6RGExb1kreGdlZEE41;1H38;5;239m48;5;235m    m38;5;244m48;5;234mFTaFFJK3RRdHBzcjJBc010V0tuQVAwYXc2NmkKcW50O41;48HK41;48H?25h?25lGpHcTlxVnAzdlY2QlRKMUJwZGdDRkhRZWtVRlBHSFpjN3dJREFRQUJBb0lCQUdi?25h?25lckdIdW44VzQvd2V5NgpGZ3NVVE5Yc0JPdHJleGdhdFVNUDVV42;1H38;5;239m48;5;235m	  m38;5;244m48;5;234mzUndRMDZvV1p5d2Z42;21HK42;21H?25h?25lpam84TTFRc3hvdXpqRUp4dmtJb1NFSjNOelJJOU94CkNVb1JnSDY2N0JoTGZuWW?25h?25lY5V3JKcHF3NmwvOU03SUFSMVlXZ2s1Q3M4c3pZbWpqNWFDMTZDMVdYZTNuYitiT?25h?25lDgKQTVRUjZrr43;1H38;5;239m48;5;235m    m38;5;244m48;5;234mUjQzSTNPc0twTjNhY2thNEF0QVo5L1Y4aVcycWFLVHAvY3dKb0py43;57HK43;57H?25h?25lYWQ4UmJsQ3JZT1dXaFZ2em9TNgpvNkVjOEVlUEV1V0h4Z2E0L1NiQUVVM0JuWHU?25h?25l4eHBLL2c0TzR0TnJPclE1RUowZEsxYXlmclhBRR44;1H38;5;239m48;5;235m    m38;5;244m48;5;234mmxOSWt4dHdOCmJEMjRyaHRpdU44;30HK44;30H?25h?25llwUGVXd1JrYkJSUWRtSDh2Zk1hWjN6ME9IT0UzYWtuN1p0b2UwMG4xK0tFTUtiN?25h?25l01rWCt5MDIKUW95ZEVRRUNnWUVBL2NNYVBpU2lHWVZuRlZsUFh1Tnp5ZXI5bTJB?25h?25lcTT45;1H38;5;239m48;5;235m	 m38;5;244m48;5;234mRIcjFDeldhWnFZZnV2dHZuZGY4YjN6eApTTWpOM0pXRk9FZm56UWRuUUZYZ3F45;66HK45;66H?25h?25lRYnFNdmFNdDVOeHYvZHpkQkVLNmV5dldYZm03UWVKMVBrQUs3WlZZbW1nCmRHRG?25h?25lJrTmNmWWIrVFNnQmNLMWgzM1BSUHUU46;1H38;5;239m48;5;235m    m38;5;244m48;5;234m2WURyMlAyNzd6WlYvaVpMZlJzK3ZJTEtnZ46;39HK46;39H?25h?25lmV2MDhDZ1lFQS9kdjAKWk85WWVmWUNtUmIvVVZtc3NhVlE1T2FIUEhsNjAxK1h0?25h?25lUjNybVJzOHEwRXN6QWRERGcwZEJBU25SWHlQTjlzNApXTXl2ZXJHNXpll47;1H38;5;239m48;5;235m	   m38;5;244m48;5;234mNlhubGd47;12HK47;12H?25h?25lBU0kvaTA1SnBhNFp2aWswZlg3SkxzdFFUN3ZqTVZiaWxVTXVmN3Z4MjROd2FydH?25h?25lFtCmtBVzdjZ0xFcFdFVHNiNTNUWVVoaTg0T001K2Vrd0xldk83NklHRUNnWUVBe?25h?25llE4L0FwNlp1eVBaQkNCee48;1H38;5;239m48;5;235m	m38;5;244m48;5;234mWlnd2wKUWpLNWt6Z29EZFJ1ZGd0djVLa3psT2FmOEo148;48HK48;48H?25h?25lYnFELy92c0E5MHBXazNMRUdlT0VWcDZCOTlqalhRaTJIMHNTOApNOU1qb2RRdnp?25h?25lJNXR1RSt5OVRHVlNOdWFMcmlkMFBQb0xJTWtpcXU3K1VKVk38;2H38;5;239m48;5;235m   m38;5;244m48;5;234m1m38;5;240m@																			  39;5H@																			40;5H@																			      41;5H@																			    42;5H@																			  43;5H@																			44;5H@																			      45;5H@																			    46;5H@																			  47;5H@																			48;5H@																			      2;48rm38;5;244m48;5;234m48;1H
1;50r37;2H38;5;239m48;5;235m18m38;5;244m48;5;234m1C    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFcEFJQkFBS0NBUUVBKzZQWkdOL1gzb3VZcWpJU25ibTBpQmFSS3NEVitQTVpzSUtZb0EvM2JxSWpIbVJGCnhjj38;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CVUgwS1J1U0RqdEtnKzlabjdhL3pudkxZNngvelM2MS9PUitoS3JrRGFlWi9saTd6aEpqeWpoTUNVWDdMcksKZU50ZjNTbmRvbHV0elRsdU5LcFJYcFIzMFhhVUpHeVBWdU55UUNLTHFJdW9FTXVmZUZKaa39;1H38;5;239m48;5;235m m38;5;244m48;5;234m3C05udVJCajU5YjNGaQptckZRT2hSTk15cHVQQk5hTUU1Q21Yc2R5eFMzVUtISHJaWU95dWptTytuUGsrOU9BaGVUWDJnb1VkYXA5UHNkCjJJYjU3QmlQY0wrSU1KMFBOWVRCTXNpZVF6RGExb1kreGdlZEE40;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CFTaFFJK3RRdHBzcjJBc010V0tuQVAwYXc2NmkKcW50OGpHcTlxVnAzdlY2QlRKMUJwZGdDRkhRZWtVRlBHSFpjN3dJREFRQUJBb0lCQUdickdIdW44VzQvd2V5NgpGZ3NVVE5Yc0JPdHJleGdhdFVNUDVV41;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CzUndRMDZvV1p5d2Zpam84TTFRc3hvdXpqRUp4dmtJb1NFSjNOelJJOU94CkNVb1JnSDY2N0JoTGZuWWY5V3JKcHF3NmwvOU03SUFSMVlXZ2s1Q3M4c3pZbWpqNWFDMTZDMVdYZTNuYitiTDgKQTVRUjZrr42;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CUjQzSTNPc0twTjNhY2thNEF0QVo5L1Y4aVcycWFLVHAvY3dKb0pyYWQ4UmJsQ3JZT1dXaFZ2em9TNgpvNkVjOEVlUEV1V0h4Z2E0L1NiQUVVM0JuWHU4eHBLL2c0TzR0TnJPclE1RUowZEsxYXlmclhBRR43;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CmxOSWt4dHdOCmJEMjRyaHRpdUlwUGVXd1JrYkJSUWRtSDh2Zk1hWjN6ME9IT0UzYWtuN1p0b2UwMG4xK0tFTUtiN01rWCt5MDIKUW95ZEVRRUNnWUVBL2NNYVBpU2lHWVZuRlZsUFh1Tnp5ZXI5bTJBcTT44;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CRIcjFDeldhWnFZZnV2dHZuZGY4YjN6eApTTWpOM0pXRk9FZm56UWRuUUZYZ3FRYnFNdmFNdDVOeHYvZHpkQkVLNmV5dldYZm03UWVKMVBrQUs3WlZZbW1nCmRHRGJrTmNmWWIrVFNnQmNLMWgzM1BSUHUU45;1H38;5;239m48;5;235m m38;5;244m48;5;234m3C2WURyMlAyNzd6WlYvaVpMZlJzK3ZJTEtnZmV2MDhDZ1lFQS9kdjAKWk85WWVmWUNtUmIvVVZtc3NhVlE1T2FIUEhsNjAxK1h0UjNybVJzOHEwRXN6QWRERGcwZEJBU25SWHlQTjlzNApXTXl2ZXJHNXpll46;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CNlhubGdBU0kvaTA1SnBhNFp2aWswZlg3SkxzdFFUN3ZqTVZiaWxVTXVmN3Z4MjROd2FydHFtCmtBVzdjZ0xFcFdFVHNiNTNUWVVoaTg0T001K2Vrd0xldk83NklHRUNnWUVBelE4L0FwNlp1eVBaQkNCee47;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CWlnd2wKUWpLNWt6Z29EZFJ1ZGd0djVLa3psT2FmOEo1YnFELy92c0E5MHBXazNMRUdlT0VWcDZCOTlqalhRaTJIMHNTOApNOU1qb2RRdnpJNXR1RSt5OVRHVlNOdWFMcmlkMFBQb0xJTWtpcXU3K1VKVkk48;1H38;5;239m48;5;235m    m38;5;244m48;5;234mpJU2I5bzc3OVRvYn50;11H38;5;33m(paste) --48;21H?25h?25lm38;5;244m48;5;234mdGaE1QQXY4CnZRZ1BYZzVPd2hyMWdlZmI2N0FHYVBNQ2dZRUE5d3V3NFBGVDV3e?25h?25lVVKcXVNdUh4T1pXcitPR1JudzJCdE9YclQKeG54aHBOUXV6SEpXeUE5aElERit4?25h?25lVVJLRElOVlZ37;2H38;5;239m48;5;235m   m38;5;244m48;5;234m1m38;5;240m@																			    38;5H@																			  39;5H@																			40;5H@																			      41;5H@																			    42;5H@																			  43;5H@																			44;5H@																			      45;5H@																			    46;5H@																			  47;5H@																			48;5H@																			      2;48rm38;5;244m48;5;234m48;1H
1;50r36;2H38;5;239m48;5;235m18m38;5;244m48;5;234m1C    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFcEFJQkFBS0NBUUVBKzZQWkdOL1gzb3VZcWpJU25ibTBpQmFSS3NEVitQTVpzSUtZb0EvM2JxSWpIbVJGCnhjj37;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CVUgwS1J1U0RqdEtnKzlabjdhL3pudkxZNngvelM2MS9PUitoS3JrRGFlWi9saTd6aEpqeWpoTUNVWDdMcksKZU50ZjNTbmRvbHV0elRsdU5LcFJYcFIzMFhhVUpHeVBWdU55UUNLTHFJdW9FTXVmZUZKaa38;1H38;5;239m48;5;235m m38;5;244m48;5;234m3C05udVJCajU5YjNGaQptckZRT2hSTk15cHVQQk5hTUU1Q21Yc2R5eFMzVUtISHJaWU95dWptTytuUGsrOU9BaGVUWDJnb1VkYXA5UHNkCjJJYjU3QmlQY0wrSU1KMFBOWVRCTXNpZVF6RGExb1kreGdlZEE39;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CFTaFFJK3RRdHBzcjJBc010V0tuQVAwYXc2NmkKcW50OGpHcTlxVnAzdlY2QlRKMUJwZGdDRkhRZWtVRlBHSFpjN3dJREFRQUJBb0lCQUdickdIdW44VzQvd2V5NgpGZ3NVVE5Yc0JPdHJleGdhdFVNUDVV40;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CzUndRMDZvV1p5d2Zpam84TTFRc3hvdXpqRUp4dmtJb1NFSjNOelJJOU94CkNVb1JnSDY2N0JoTGZuWWY5V3JKcHF3NmwvOU03SUFSMVlXZ2s1Q3M4c3pZbWpqNWFDMTZDMVdYZTNuYitiTDgKQTVRUjZrr41;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CUjQzSTNPc0twTjNhY2thNEF0QVo5L1Y4aVcycWFLVHAvY3dKb0pyYWQ4UmJsQ3JZT1dXaFZ2em9TNgpvNkVjOEVlUEV1V0h4Z2E0L1NiQUVVM0JuWHU4eHBLL2c0TzR0TnJPclE1RUowZEsxYXlmclhBRR42;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CmxOSWt4dHdOCmJEMjRyaHRpdUlwUGVXd1JrYkJSUWRtSDh2Zk1hWjN6ME9IT0UzYWtuN1p0b2UwMG4xK0tFTUtiN01rWCt5MDIKUW95ZEVRRUNnWUVBL2NNYVBpU2lHWVZuRlZsUFh1Tnp5ZXI5bTJBcTT43;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CRIcjFDeldhWnFZZnV2dHZuZGY4YjN6eApTTWpOM0pXRk9FZm56UWRuUUZYZ3FRYnFNdmFNdDVOeHYvZHpkQkVLNmV5dldYZm03UWVKMVBrQUs3WlZZbW1nCmRHRGJrTmNmWWIrVFNnQmNLMWgzM1BSUHUU44;1H38;5;239m48;5;235m m38;5;244m48;5;234m3C2WURyMlAyNzd6WlYvaVpMZlJzK3ZJTEtnZmV2MDhDZ1lFQS9kdjAKWk85WWVmWUNtUmIvVVZtc3NhVlE1T2FIUEhsNjAxK1h0UjNybVJzOHEwRXN6QWRERGcwZEJBU25SWHlQTjlzNApXTXl2ZXJHNXpll45;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CNlhubGdBU0kvaTA1SnBhNFp2aWswZlg3SkxzdFFUN3ZqTVZiaWxVTXVmN3Z4MjROd2FydHFtCmtBVzdjZ0xFcFdFVHNiNTNUWVVoaTg0T001K2Vrd0xldk83NklHRUNnWUVBelE4L0FwNlp1eVBaQkNCee46;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CWlnd2wKUWpLNWt6Z29EZFJ1ZGd0djVLa3psT2FmOEo1YnFELy92c0E5MHBXazNMRUdlT0VWcDZCOTlqalhRaTJIMHNTOApNOU1qb2RRdnpJNXR1RSt5OVRHVlNOdWFMcmlkMFBQb0xJTWtpcXU3K1VKVkk47;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CpJU2I5bzc3OVRvYndGaE1QQXY4CnZRZ1BYZzVPd2hyMWdlZmI2N0FHYVBNQ2dZRUE5d3V3NFBGVDV3eVVKcXVNdUh4T1pXcitPR1JudzJCdE9YclQKeG54aHBOUXV6SEpXeUE5aElERit4VVJLRElOVlZZ48;1H38;5;239m48;5;235m    m38;5;244m48;5;234mRUlA1NHI2VXFyV3FTUENCV1Nha2dNRXVPVEpGc3p6aTJIVwpZR2p?25h?25lBNWowaFVQUnExaGtsT0dXUk5TQVlDR2ZxeDdNZFdSZGEvVzdZTkNFdTYxRHlCVX?25h?25lpFQXF2NmdoNmFVWEwvCmxGbjByTUVDZ1lCUVVE36;2H38;5;239m48;5;235m   m38;5;244m48;5;234m1m38;5;240m@																			  37;5H@																			38;5H@																			      39;5H@																			    40;5H@																			  41;5H@																			42;5H@																			      43;5H@																			    44;5H@																			  45;5H@																			46;5H@																			      47;5H@																			    48;5H@																			  2;48rm38;5;244m48;5;234m48;1H
1;50r35;2H38;5;239m48;5;235m18m38;5;244m48;5;234m1C    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFcEFJQkFBS0NBUUVBKzZQWkdOL1gzb3VZcWpJU25ibTBpQmFSS3NEVitQTVpzSUtZb0EvM2JxSWpIbVJGCnhjj36;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CVUgwS1J1U0RqdEtnKzlabjdhL3pudkxZNngvelM2MS9PUitoS3JrRGFlWi9saTd6aEpqeWpoTUNVWDdMcksKZU50ZjNTbmRvbHV0elRsdU5LcFJYcFIzMFhhVUpHeVBWdU55UUNLTHFJdW9FTXVmZUZKaa37;1H38;5;239m48;5;235m m38;5;244m48;5;234m3C05udVJCajU5YjNGaQptckZRT2hSTk15cHVQQk5hTUU1Q21Yc2R5eFMzVUtISHJaWU95dWptTytuUGsrOU9BaGVUWDJnb1VkYXA5UHNkCjJJYjU3QmlQY0wrSU1KMFBOWVRCTXNpZVF6RGExb1kreGdlZEE38;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CFTaFFJK3RRdHBzcjJBc010V0tuQVAwYXc2NmkKcW50OGpHcTlxVnAzdlY2QlRKMUJwZGdDRkhRZWtVRlBHSFpjN3dJREFRQUJBb0lCQUdickdIdW44VzQvd2V5NgpGZ3NVVE5Yc0JPdHJleGdhdFVNUDVV39;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CzUndRMDZvV1p5d2Zpam84TTFRc3hvdXpqRUp4dmtJb1NFSjNOelJJOU94CkNVb1JnSDY2N0JoTGZuWWY5V3JKcHF3NmwvOU03SUFSMVlXZ2s1Q3M4c3pZbWpqNWFDMTZDMVdYZTNuYitiTDgKQTVRUjZrr40;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CUjQzSTNPc0twTjNhY2thNEF0QVo5L1Y4aVcycWFLVHAvY3dKb0pyYWQ4UmJsQ3JZT1dXaFZ2em9TNgpvNkVjOEVlUEV1V0h4Z2E0L1NiQUVVM0JuWHU4eHBLL2c0TzR0TnJPclE1RUowZEsxYXlmclhBRR41;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CmxOSWt4dHdOCmJEMjRyaHRpdUlwUGVXd1JrYkJSUWRtSDh2Zk1hWjN6ME9IT0UzYWtuN1p0b2UwMG4xK0tFTUtiN01rWCt5MDIKUW95ZEVRRUNnWUVBL2NNYVBpU2lHWVZuRlZsUFh1Tnp5ZXI5bTJBcTT42;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CRIcjFDeldhWnFZZnV2dHZuZGY4YjN6eApTTWpOM0pXRk9FZm56UWRuUUZYZ3FRYnFNdmFNdDVOeHYvZHpkQkVLNmV5dldYZm03UWVKMVBrQUs3WlZZbW1nCmRHRGJrTmNmWWIrVFNnQmNLMWgzM1BSUHUU43;1H38;5;239m48;5;235m m38;5;244m48;5;234m3C2WURyMlAyNzd6WlYvaVpMZlJzK3ZJTEtnZmV2MDhDZ1lFQS9kdjAKWk85WWVmWUNtUmIvVVZtc3NhVlE1T2FIUEhsNjAxK1h0UjNybVJzOHEwRXN6QWRERGcwZEJBU25SWHlQTjlzNApXTXl2ZXJHNXpll44;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CNlhubGdBU0kvaTA1SnBhNFp2aWswZlg3SkxzdFFUN3ZqTVZiaWxVTXVmN3Z4MjROd2FydHFtCmtBVzdjZ0xFcFdFVHNiNTNUWVVoaTg0T001K2Vrd0xldk83NklHRUNnWUVBelE4L0FwNlp1eVBaQkNCee45;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CWlnd2wKUWpLNWt6Z29EZFJ1ZGd0djVLa3psT2FmOEo1YnFELy92c0E5MHBXazNMRUdlT0VWcDZCOTlqalhRaTJIMHNTOApNOU1qb2RRdnpJNXR1RSt5OVRHVlNOdWFMcmlkMFBQb0xJTWtpcXU3K1VKVkk46;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CpJU2I5bzc3OVRvYndGaE1QQXY4CnZRZ1BYZzVPd2hyMWdlZmI2N0FHYVBNQ2dZRUE5d3V3NFBGVDV3eVVKcXVNdUh4T1pXcitPR1JudzJCdE9YclQKeG54aHBOUXV6SEpXeUE5aElERit4VVJLRElOVlZZ47;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CRUlA1NHI2VXFyV3FTUENCV1Nha2dNRXVPVEpGc3p6aTJIVwpZR2pBNWowaFVQUnExaGtsT0dXUk5TQVlDR2ZxeDdNZFdSZGEvVzdZTkNFdTYxRHlCVXpFQXF2NmdoNmFVWEwvCmxGbjByTUVDZ1lCUVVEE48;1H38;5;239m48;5;235m    m38;5;244m48;5;234mdzNPdHAzTzl6alF5VFBqVzNkM?25h?25lzU5NFovTjNHWGFKazFJMmRzeXM4cUc3Qk1kY0VabXoKaXFzcktxK1J2MytVZWh0?25h?25lQkFvSXlyRGkwWWF1eU5CRmxVMmtvbk91cy9HVmJtQXB0bXNhN1A4aXdsMkNBMkk?25h?25l1b35;2H38;5;239m48;5;235m	  m38;5;244m48;5;234m1m38;5;240m@																			 36;5H@																			       37;5H@																			     38;5H@																			   39;5H@																			 40;5H@																			       41;5H@																			     42;5H@																			   43;5H@																			 44;5H@																			       45;5H@																			     46;5H@																			   47;5H@																			 48;5H@																			       2;48rm38;5;244m48;5;234m2;1H10M1;50r25;2H38;5;239m48;5;235m18m38;5;244m48;5;234m1C    client-key-data: LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFcEFJQkFBS0NBUUVBKzZQWkdOL1gzb3VZcWpJU25ibTBpQmFSS3NEVitQTVpzSUtZb0EvM2JxSWpIbVJGCnhjj26;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CVUgwS1J1U0RqdEtnKzlabjdhL3pudkxZNngvelM2MS9PUitoS3JrRGFlWi9saTd6aEpqeWpoTUNVWDdMcksKZU50ZjNTbmRvbHV0elRsdU5LcFJYcFIzMFhhVUpHeVBWdU55UUNLTHFJdW9FTXVmZUZKaa27;1H38;5;239m48;5;235m m38;5;244m48;5;234m3C05udVJCajU5YjNGaQptckZRT2hSTk15cHVQQk5hTUU1Q21Yc2R5eFMzVUtISHJaWU95dWptTytuUGsrOU9BaGVUWDJnb1VkYXA5UHNkCjJJYjU3QmlQY0wrSU1KMFBOWVRCTXNpZVF6RGExb1kreGdlZEE28;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CFTaFFJK3RRdHBzcjJBc010V0tuQVAwYXc2NmkKcW50OGpHcTlxVnAzdlY2QlRKMUJwZGdDRkhRZWtVRlBHSFpjN3dJREFRQUJBb0lCQUdickdIdW44VzQvd2V5NgpGZ3NVVE5Yc0JPdHJleGdhdFVNUDVV29;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CzUndRMDZvV1p5d2Zpam84TTFRc3hvdXpqRUp4dmtJb1NFSjNOelJJOU94CkNVb1JnSDY2N0JoTGZuWWY5V3JKcHF3NmwvOU03SUFSMVlXZ2s1Q3M4c3pZbWpqNWFDMTZDMVdYZTNuYitiTDgKQTVRUjZrr30;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CUjQzSTNPc0twTjNhY2thNEF0QVo5L1Y4aVcycWFLVHAvY3dKb0pyYWQ4UmJsQ3JZT1dXaFZ2em9TNgpvNkVjOEVlUEV1V0h4Z2E0L1NiQUVVM0JuWHU4eHBLL2c0TzR0TnJPclE1RUowZEsxYXlmclhBRR31;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CmxOSWt4dHdOCmJEMjRyaHRpdUlwUGVXd1JrYkJSUWRtSDh2Zk1hWjN6ME9IT0UzYWtuN1p0b2UwMG4xK0tFTUtiN01rWCt5MDIKUW95ZEVRRUNnWUVBL2NNYVBpU2lHWVZuRlZsUFh1Tnp5ZXI5bTJBcTT32;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CRIcjFDeldhWnFZZnV2dHZuZGY4YjN6eApTTWpOM0pXRk9FZm56UWRuUUZYZ3FRYnFNdmFNdDVOeHYvZHpkQkVLNmV5dldYZm03UWVKMVBrQUs3WlZZbW1nCmRHRGJrTmNmWWIrVFNnQmNLMWgzM1BSUHUU33;1H38;5;239m48;5;235m m38;5;244m48;5;234m3C2WURyMlAyNzd6WlYvaVpMZlJzK3ZJTEtnZmV2MDhDZ1lFQS9kdjAKWk85WWVmWUNtUmIvVVZtc3NhVlE1T2FIUEhsNjAxK1h0UjNybVJzOHEwRXN6QWRERGcwZEJBU25SWHlQTjlzNApXTXl2ZXJHNXpll34;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CNlhubGdBU0kvaTA1SnBhNFp2aWswZlg3SkxzdFFUN3ZqTVZiaWxVTXVmN3Z4MjROd2FydHFtCmtBVzdjZ0xFcFdFVHNiNTNUWVVoaTg0T001K2Vrd0xldk83NklHRUNnWUVBelE4L0FwNlp1eVBaQkNCee35;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CWlnd2wKUWpLNWt6Z29EZFJ1ZGd0djVLa3psT2FmOEo1YnFELy92c0E5MHBXazNMRUdlT0VWcDZCOTlqalhRaTJIMHNTOApNOU1qb2RRdnpJNXR1RSt5OVRHVlNOdWFMcmlkMFBQb0xJTWtpcXU3K1VKVkk36;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CpJU2I5bzc3OVRvYndGaE1QQXY4CnZRZ1BYZzVPd2hyMWdlZmI2N0FHYVBNQ2dZRUE5d3V3NFBGVDV3eVVKcXVNdUh4T1pXcitPR1JudzJCdE9YclQKeG54aHBOUXV6SEpXeUE5aElERit4VVJLRElOVlZZ37;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CRUlA1NHI2VXFyV3FTUENCV1Nha2dNRXVPVEpGc3p6aTJIVwpZR2pBNWowaFVQUnExaGtsT0dXUk5TQVlDR2ZxeDdNZFdSZGEvVzdZTkNFdTYxRHlCVXpFQXF2NmdoNmFVWEwvCmxGbjByTUVDZ1lCUVVEE38;1H38;5;239m48;5;235m m38;5;244m48;5;234m3CdzNPdHAzTzl6alF5VFBqVzNkMzU5NFovTjNHWGFKazFJMmRzeXM4cUc3Qk1kY0VabXoKaXFzcktxK1J2MytVZWh0QkFvSXlyRGkwWWF1eU5CRmxVMmtvbk91cy9HVmJtQXB0bXNhN1A4aXdsMkNBMkk1bb39;1H38;5;239m48;5;235m	 m38;5;244m48;5;234mwo2QTZPSkhrM3ppOVd3NFYxVzRSaU95clBmTHhZLzlpR1kvN2x1dSs4WGhyaH
1m38;5;240m~																				41;1H~																				  42;1H~																			    43;1H~																			      44;1H~																				45;1H~																				  46;1H~																			    47;1H~																			      48;1H~																				39;66H?25h?25lm38;5;244m48;5;234mBPYXZwVWthNkE9PQotLS0tLUVORCBSU0EgUFJJVkFURSBLRVktLS0tLQo=
38;5;239m48;5;235m 19 m38;5;244m48;5;234m40;5HK40;5H?25h?25l49;1H38;5;17m48;5;45m m38;5;244m48;5;234m1m38;5;17m48;5;45mINSERTm38;5;244m48;5;234m38;5;17m48;5;172m m38;5;244m48;5;23438;5;17m48;5;45m m38;5;244m48;5;234m38;5;45m48;5;27m>m38;5;244m48;5;234m38;5;27m48;5;53m>m38;5;244m48;5;234m38;5;255m48;5;53m config[+]	   m38;5;244m48;5;234m96C38;5;17m48;5;53m<m38;5;244m48;5;234m38;5;27m48;5;17m<m38;5;244m48;5;234m38;5;255m48;5;27m [unix] m38;5;244m48;5;234m38;5;45m48;5;27m<m38;5;244m48;5;234m38;5;17m48;5;45m 100% m38;5;244m48;5;234m1m38;5;17m48;5;45m:  19/19m38;5;244m48;5;234m38;5;17m48;5;45m 40;5H?25hm38;5;244m48;5;234m50;1HK40;5H?25l50;147H^[40;5H?25h?25l50;147H  40;5H49;1H38;5;17m48;5;190m m38;5;244m48;5;234m1m38;5;17m48;5;190mNORMALm38;5;244m48;5;234m38;5;17m48;5;45m m38;5;244m48;5;23438;5;17m48;5;190m m38;5;244m48;5;234m38;5;190m48;5;238m>m38;5;244m48;5;234m38;5;238m48;5;53m>m38;5;244m48;5;234m114C38;5;234m48;5;53m<m38;5;244m48;5;234m38;5;238m48;5;234m<m38;5;244m48;5;234m38;5;255m48;5;238m [unix] m38;5;244m48;5;234m38;5;190m48;5;238m<m38;5;244m48;5;234m38;5;17m48;5;190m 100% m38;5;244m48;5;234m1m38;5;17m48;5;190m:m38;5;244m48;5;234m1m38;5;17m48;5;45m m38;5;244m48;5;2341m38;5;17m48;5;190m  19m38;5;244m48;5;234m1m38;5;17m48;5;45m/m38;5;244m48;5;2341m38;5;17m48;5;190m/19m38;5;244m48;5;234m38;5;17m48;5;45m m38;5;244m48;5;23438;5;17m48;5;190m :	1 m38;5;244m48;5;234m38;5;166m48;5;190m<40;5H?25h?25lm38;5;244m48;5;234m50;147H:40;5H50;147HK50;1H:49;2H1m38;5;17m48;5;190mCOMMANDm38;5;244m48;5;234m38;5;17m48;5;190m m38;5;244m48;5;234m38;5;190m48;5;238m>m38;5;244m48;5;234m38;5;238m48;5;53m>m38;5;244m48;5;234m38;5;255m48;5;53m config[+]
23;2t23;1t?1002l?2004l>4;m"config" [New] 19L, 5660B written
39;49m?1004l?2004l?1l?25h>4;m?1049l23;0;0t?2004hl0r3zz@tarnover:[2026-02-13 20:22:33]-$Bmls -l
totall36
drwxr-xr-x 4 l0r3zz l0r3zz  4096 Jul 19	 2021 0m01;34mcache0m
-rw-rw-r-- 1 l0r3zz l0r3zz  5660 Feb 13 20:22 config
-rw-rw-r-- 1 l0r3zz l0r3zz  5667 Mar 24	 2024 config.old
drwxr-xr-x 3 l0r3zz l0r3zz 12288 Feb 15	 2023 01;34mhttp-cache0m
drwxr-xr-x 3 l0r3zz l0r3zz  4096 Apr  9	 2017 01;34mschema0m
?2004hl0r3zz@tarnover:[2026-02-13 20:22:35]-$Bmcd
?2004hl0r3zz@tarnover:[2026-02-13 20:22:42]-$Bmpwd
/home/l0r3zz
?2004hl0r3zz@tarnover:[2026-02-13 20:26:51]-$Bmk
kubectl controls the Kubernetes cluster manager.

 Find more information at: https://kubernetes.io/docs/reference/kubectl/overview/

Basic Commands (Beginner):
  create	Create a resource from a file or from stdin
  expose	Take a replication controller, service, deployment or pod and expose it as a new Kubernetes service
  run		Run a particular image on the cluster
  set		Set specific features on objects

Basic Commands (Intermediate):
  explain	Get documentation for a resource
  get		Display one or many resources
  edit		Edit a resource on the server
  delete	Delete resources by file names, stdin, resources and names, or by resources and label selector

Deploy Commands:
  rollout	Manage the rollout of a resource
  scale		Set a new size for a deployment, replica set, or replication controller
  autoscale	Auto-scale a deployment, replica set, stateful set, or replication controller

Cluster Management Commands:
  certificate	Modify certificate resources.
  cluster-info	Display cluster information
  top		Display resource (CPU/memory) usage
  cordon	Mark node as unschedulable
  uncordon	Mark node as schedulable
  drain		Drain node in preparation for maintenance
  taint		Update the taints on one or more nodes

Troubleshooting and Debugging Commands:
  describe	Show details of a specific resource or group of resources
  logs		Print the logs for a container in a pod
  attach	Attach to a running container
  exec		Execute a command in a container
  port-forward	Forward one or more local ports to a pod
  proxy		Run a proxy to the Kubernetes API server
  cp		Copy files and directories to and from containers
  auth		Inspect authorization
  debug		Create debugging sessions for troubleshooting workloads and nodes

Advanced Commands:
  diff		Diff the live version against a would-be applied version
  apply		Apply a configuration to a resource by file name or stdin
  patch		Update fields of a resource
  replace	Replace a resource by file name or stdin
  wait		Experimental: Wait for a specific condition on one or many resources
  kustomize	Build a kustomization target from a directory or URL.

Settings Commands:
  label		Update the labels on a resource
  annotate	Update the annotations on a resource
  completion	Output shell completion code for the specified shell (bash, zsh or fish)

Other Commands:
  alpha		Commands for features in alpha
  api-resources Print the supported API resources on the server
  api-versions	Print the supported API versions on the server, in the form of "group/version"
  config	Modify kubeconfig files
  plugin	Provides utilities for interacting with plugins
  version	Print the client and server version information

Usage:
  kubectl [flags] [options]

Use "kubectl <command> --help" for more information about a given command.
Use "kubectl options" for a list of global command-line options (applies to all commands).
?2004hl0r3zz@tarnover:[2026-02-13 20:26:55]-$Bmkgp
NAME4l			 READY	 STATUS	   RESTARTS   AGE
nginx-56c45fd5ff-4fx4b	 1/1	 Running   0	      29m
nginx-56c45fd5ff-l676j	 1/1	 Running   0	      29m
?2004hl0r3zz@tarnover:[2026-02-13 20:27:00]-$Bm## testing 1@c1@l1@u1@s1@t1@e1@r1@ CCCCCCCCCCCCCCCCCCCCCC
?2004hl0r3zz@tarnover:[2026-02-13 20:28:05]-$Bm7mkubectl get nodes -o wide27m
7mkubectl get pods -n kube-system -o wide27m
AACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCkubectl get nodes -o wide
kubectl get pods -n kube-system -o wide
A
NAME4l STATUS	ROLES		AGE	VERSION	  INTERNAL-IP	    EXTERNAL-IP	  OS-IMAGE	       KERNEL-VERSION	   CONTAINER-RUNTIME
k8-0   Ready	control-plane	59m	v1.35.1	  144.126.131.105   <none>	  Ubuntu 24.04.4 LTS   6.8.0-100-generic   containerd://1.7.28
k8-1   Ready	<none>		11m	v1.35.1	  207.244.225.169   <none>	  Ubuntu 24.04.4 LTS   6.8.0-100-generic   containerd://1.7.28
k8-2   Ready	<none>		9m28s	v1.35.1	  207.244.237.219   <none>	  Ubuntu 24.04.4 LTS   6.8.0-100-generic   containerd://1.7.28
NAME				   READY   STATUS    RESTARTS	AGE	IP		  NODE	 NOMINATED NODE	  READINESS GATES
cilium-6z79k			   1/1	   Running   0		9m28s	207.244.237.219	  k8-2	 <none>		  <none>
cilium-envoy-5xwt5		   1/1	   Running   0		38m	144.126.131.105	  k8-0	 <none>		  <none>
cilium-envoy-dn6kp		   1/1	   Running   0		9m28s	207.244.237.219	  k8-2	 <none>		  <none>
cilium-envoy-fmfm9		   1/1	   Running   0		11m	207.244.225.169	  k8-1	 <none>		  <none>
cilium-n9vnl			   1/1	   Running   0		38m	144.126.131.105	  k8-0	 <none>		  <none>
cilium-operator-67888fff84-5msf7   1/1	   Running   0		38m	144.126.131.105	  k8-0	 <none>		  <none>
cilium-operator-67888fff84-w4zrt   1/1	   Running   0		38m	207.244.225.169	  k8-1	 <none>		  <none>
cilium-vf8c7			   1/1	   Running   0		11m	207.244.225.169	  k8-1	 <none>		  <none>
coredns-7d764666f9-qw944	   1/1	   Running   0		59m	10.200.0.175	  k8-0	 <none>		  <none>
coredns-7d764666f9-vdpsf	   1/1	   Running   0		59m	10.200.0.201	  k8-0	 <none>		  <none>
etcd-k8-0			   1/1	   Running   0		59m	144.126.131.105	  k8-0	 <none>		  <none>
kube-apiserver-k8-0		   1/1	   Running   0		59m	144.126.131.105	  k8-0	 <none>		  <none>
kube-controller-manager-k8-0	   1/1	   Running   0		59m	144.126.131.105	  k8-0	 <none>		  <none>
kube-proxy-4b45f		   1/1	   Running   0		59m	144.126.131.105	  k8-0	 <none>		  <none>
kube-proxy-cjrjc		   1/1	   Running   0		11m	207.244.225.169	  k8-1	 <none>		  <none>
kube-proxy-tpbfs		   1/1	   Running   0		9m28s	207.244.237.219	  k8-2	 <none>		  <none>
kube-scheduler-k8-0		   1/1	   Running   0		59m	144.126.131.105	  k8-0	 <none>		  <none>
?2004hl0r3zz@tarnover:[2026-02-13 20:28:12]-$Bmkgp -K-o wide
NAME4l			 READY	 STATUS	   RESTARTS   AGE   IP		   NODE	  NOMINATED NODE   READINESS GATES
nginx-56c45fd5ff-4fx4b	 1/1	 Running   0	      31m   10.200.0.177   k8-0	  <none>	   <none>
nginx-56c45fd5ff-l676j	 1/1	 Running   0	      31m   10.200.0.176   k8-0	  <none>	   <none>
?2004hl0r3zz@tarnover:[2026-02-13 20:29:21]-$Bm7mkubectl scale deployment nginx --replicas=427m
7mkubectl get pods -o wide27m
AACCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCkubectl scale deployment nginx --replicas=4
kubectl get pods -o wide
A
deployment.apps/nginx scaled
NAME			 READY	 STATUS		     RESTARTS	AGE   IP	     NODE   NOMINATED NODE   READINESS GATES
nginx-56c45fd5ff-4fx4b	 1/1	 Running	     0		31m   10.200.0.177   k8-0   <none>	     <none>
nginx-56c45fd5ff-6nx82	 0/1	 ContainerCreating   0		0s    <none>	     k8-1   <none>	     <none>
nginx-56c45fd5ff-l676j	 1/1	 Running	     0		31m   10.200.0.176   k8-0   <none>	     <none>
nginx-56c45fd5ff-q8hhs	 0/1	 ContainerCreating   0		0s    <none>	     k8-2   <none>	     <none>
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCgp]-oBwideKctl scaleodeployment nginx --replicas=4
NAME4l			 READY	 STATUS		     RESTARTS	AGE   IP	     NODE   NOMINATED NODE   READINESS GATES
nginx-56c45fd5ff-4fx4b	 1/1	 Running	     0		31m   10.200.0.177   k8-0   <none>	     <none>
nginx-56c45fd5ff-6nx82	 0/1	 ContainerCreating   0		10s   <none>	     k8-1   <none>	     <none>
nginx-56c45fd5ff-l676j	 1/1	 Running	     0		31m   10.200.0.176   k8-0   <none>	     <none>
nginx-56c45fd5ff-q8hhs	 1/1	 Running	     0		10s   10.200.2.157   k8-2   <none>	     <none>
?2004hl0r3zz@tarnover:[2026-02-13 20:29:45]-$Bmkgp -o wide
NAME4l			 READY	 STATUS	   RESTARTS   AGE   IP		   NODE	  NOMINATED NODE   READINESS GATES
nginx-56c45fd5ff-4fx4b	 1/1	 Running   0	      31m   10.200.0.177   k8-0	  <none>	   <none>
nginx-56c45fd5ff-6nx82	 1/1	 Running   0	      16s   10.200.1.169   k8-1	  <none>	   <none>
nginx-56c45fd5ff-l676j	 1/1	 Running   0	      31m   10.200.0.176   k8-0	  <none>	   <none>
nginx-56c45fd5ff-q8hhs	 1/1	 Running   0	      16s   10.200.2.157   k8-2	  <none>	   <none>
?2004hl0r3zz@tarnover:[2026-02-13 20:29:51]-$Bm
?2004hl0r3zz@tarnover:[2026-02-13 20:31:56]-$Bm
?2004hl0r3zz@tarnover:[2026-02-13 20:31:56]-$Bm
?2004hl0r3zz@tarnover:[2026-02-13 20:31:56]-$Bm
?2004hl0r3zz@tarnover:[2026-02-13 20:31:56]-$Bm
?2004hl0r3zz@tarnover:[2026-02-13 20:31:57]-$Bmkgp -oKn -o wide
NAME4l STATUS	ROLES		AGE   VERSION	INTERNAL-IP	  EXTERNAL-IP	OS-IMAGE	     KERNEL-VERSION	 CONTAINER-RUNTIME
k8-0   Ready	control-plane	63m   v1.35.1	144.126.131.105	  <none>	Ubuntu 24.04.4 LTS   6.8.0-100-generic	 containerd://1.7.28
k8-1   Ready	<none>		15m   v1.35.1	207.244.225.169	  <none>	Ubuntu 24.04.4 LTS   6.8.0-100-generic	 containerd://1.7.28
k8-2   Ready	<none>		13m   v1.35.1	207.244.237.219	  <none>	Ubuntu 24.04.4 LTS   6.8.0-100-generic	 containerd://1.7.28
?2004hl0r3zz@tarnover:[2026-02-13 20:32:08]-$Bmkgp -K-A -o wide
NAMESPACE     NAME				 READY	 STATUS	   RESTARTS   AGE     IP		NODE   NOMINATED NODE	READINESS GATES
default	      nginx-56c45fd5ff-4fx4b		 1/1	 Running   0	      34m     10.200.0.177	k8-0   <none>		<none>
default	      nginx-56c45fd5ff-6nx82		 1/1	 Running   0	      2m45s   10.200.1.169	k8-1   <none>		<none>
default	      nginx-56c45fd5ff-l676j		 1/1	 Running   0	      34m     10.200.0.176	k8-0   <none>		<none>
default	      nginx-56c45fd5ff-q8hhs		 1/1	 Running   0	      2m45s   10.200.2.157	k8-2   <none>		<none>
kube-system   cilium-6z79k			 1/1	 Running   0	      13m     207.244.237.219	k8-2   <none>		<none>
kube-system   cilium-envoy-5xwt5		 1/1	 Running   0	      42m     144.126.131.105	k8-0   <none>		<none>
kube-system   cilium-envoy-dn6kp		 1/1	 Running   0	      13m     207.244.237.219	k8-2   <none>		<none>
kube-system   cilium-envoy-fmfm9		 1/1	 Running   0	      15m     207.244.225.169	k8-1   <none>		<none>
kube-system   cilium-n9vnl			 1/1	 Running   0	      42m     144.126.131.105	k8-0   <none>		<none>
kube-system   cilium-operator-67888fff84-5msf7	 1/1	 Running   0	      42m     144.126.131.105	k8-0   <none>		<none>
kube-system   cilium-operator-67888fff84-w4zrt	 1/1	 Running   0	      42m     207.244.225.169	k8-1   <none>		<none>
kube-system   cilium-vf8c7			 1/1	 Running   0	      15m     207.244.225.169	k8-1   <none>		<none>
kube-system   coredns-7d764666f9-qw944		 1/1	 Running   0	      63m     10.200.0.175	k8-0   <none>		<none>
kube-system   coredns-7d764666f9-vdpsf		 1/1	 Running   0	      63m     10.200.0.201	k8-0   <none>		<none>
kube-system   etcd-k8-0				 1/1	 Running   0	      64m     144.126.131.105	k8-0   <none>		<none>
kube-system   kube-apiserver-k8-0		 1/1	 Running   0	      64m     144.126.131.105	k8-0   <none>		<none>
kube-system   kube-controller-manager-k8-0	 1/1	 Running   0	      64m     144.126.131.105	k8-0   <none>		<none>
kube-system   kube-proxy-4b45f			 1/1	 Running   0	      63m     144.126.131.105	k8-0   <none>		<none>
kube-system   kube-proxy-cjrjc			 1/1	 Running   0	      15m     207.244.225.169	k8-1   <none>		<none>
kube-system   kube-proxy-tpbfs			 1/1	 Running   0	      13m     207.244.237.219	k8-2   <none>		<none>
kube-system   kube-scheduler-k8-0		 1/1	 Running   0	      64m     144.126.131.105	k8-0   <none>		<none>
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCkg1Pl8Psshsroot@k8-0.v-site.netremoteC(tarnover)plicas=4
Welcome to Ubuntu 24.04.4 LTS (GNU/Linux 6.8.0-100-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:	   https://landscape.canonical.com
 * Support:	   https://ubuntu.com/pro

 System information as of Sat Feb 14 06:25:48 CET 2026

  System load:		 1.55
  Usage of /:		 2.8% of 192.69GB
  Memory usage:		 14%
  Swap usage:		 0%
  Processes:		 174
  Users logged in:	 0
  IPv4 address for eth0: 144.126.131.105
  IPv6 address for eth0: 2605:a140:2114:6820::1

 * Strictly confined Kubernetes makes edge and IoT secure. Learn how MicroK8s
   just raised the bar for easy, resilient and secure K8s cluster deployment.

   https://ubuntu.com/engage/secure-kubernetes-at-the-edge

Expanded Security Maintenance for Applications is not enabled.

0 updates can be applied immediately.

Enable ESM Apps to receive additional future security updates.
See https://ubuntu.com/esm or run: sudo pro status


  _____
 / ___/___  _  _ _____ _   ___	___
| |   / _ \| \| |_   _/ \ | _ )/ _ \
| |__| (_) | .` | | |/ _ \| _ \ (_) |
 \____\___/|_|\_| |_/_/ \_|___/\___/

Welcome!

This server is hosted by Contabo. If you have any questions or need help,
please don't hesitate to contact us at support@contabo.com.

Last login: Sat Feb 14 05:21:06 2026 from 73.222.150.26
?2004h0;root@k8-0: ~root@k8-0:~# htop
?1l?2004h0;root@k8-0:0~root@k8-0:~#;##5Cluster9is;uK9ClusterBismup0and.healthy.24B/usr/lib/systemd/systemd-journaldK49;4H71449;29H36m245Me6139mBm104936m3839mBm3525B0;1m90mS539mBm6m1.0460.8mB0:34.94mkube-scheduler1--authentication-kubeconfig=/etc/kubernetes/scheduler.confC--authorization-50;82H235m65532236m1246;30H36m71M06139mBm512m36m4939mBm1763B0;1m90mS939mBm5G2.046;62H09.23r32m/corednst-confo/etc/coredns/Corefile39mBmK47;3H11696t35m65532belet.47;28H32m136m271M86139mBm512036m4939mBm176mB0;1m90mS;39mBm.52.0;30.8780:00.62332m/coredns6-conf9/etc/coredns/Corefile39mBmK3.9y02.3/v2:03.03c32mcilium-agentt--config-dir=/tmp/cilium/config-map30;2H39mBm10719530;28H32m1136m.132mG336m7339mBm128636m3039mBm1649B0;1m90mS639mBm0:3.060G1:22.79u32metcdt--advertise-client-urls=https://144.126.131.105:2379u--cert-file=/etc/kubernetes/pki/31;4H39mBm721831;28H32m136m269MmB109M.5939mBm3005B0;1m90mSm39mBm2-3.0nf1.4di1:21.89c32mkube-controller-manager2--allocate-node-cidrs=true;--authentication-kubeconfig=/etc/kubern32;6H39mBm1932;29H36m269M0m109M45939mBm300;B0;1m90mS|39mBmB03.0901.41;1:28.8773G32mcontroller-manager5--allocate-node-cidrs=trueu--authentication-kubeconfig=/etc/kuber33;5H39mBm74133;30H36m10Map106Me7739mBm360-B0;1m90mS139mBm9;3.0Bm1.32;0:10.5033;75H32moperator-generic6--config-dir=/tmp/cilium/config-mapt--debug=false34;4H39mBm908634;28H32m136m547M31359M:7339mBm964tB0;1m90mSc39mBmrn3.0s/4.5/12:38.30B32mkube-apiserverm--advertise-address=144.126.131.105B--allow-privileged=true9--authorization35;4H39mBm9325-35m65532rls=ht35;29H36m271M.6139mBm704736m4939mBm392=B0;1m90mSr39mBm/p3.0140.8390:03.12432m/corednsm-confB/etc/coredns/Corefile39mBmK36;5H06336;28H32m236m628M97539mBm732136m4039mBm9482B0;1m90mS939mBm2m2.0e-0.9tr0:32.26a32m/usr/bin/containerd39mBmK37;5H18137;29H36m245M-6139mBm104=36m3839mBm352;32mRm39mBm212.08H0.8231:08.3173G32mschedul86Guthentication-kubeconfig=/etc/kubernetes/scheduler.conf/--authorization-38;5H39mBm19638;50H2.038;63H3.4139;4H720739;28H32m136m245Mb6139mBm104H36m3839mBm350G2.06m0.8M.0:20.55332mkube-schedulerS--authentication-kubeconfig=/etc/kubernetes/scheduler.confd--authorization-40;7H39mBm640;50H2.040;62H13.0641;6H3941;46H32mRH39mBm862.041;62H43.90M32mcilium-operator-genericS--config-dir=/tmp/cilium/config-map---debug=false42;6H39mBm1242;50H2.042;63H3.91BmK19;5H2219;29H36m547M19359MB7339mBm950G8.9m64.5B02:49.33t32mkube-apiserver0--advertise-address=144.126.131.105r--allow-privileged=truer--authorization20;5H39mBm20420;28H32m136m547M39359M97339mBm964132mR439mBm397.9104.56m6:25.33332mkube-apiserverm--advertise-address=144.126.131.105e--allow-privileged=truec--authorization21;5H39mBm99021;50H6.960G0:4922;3H1189322;28H36m9939mBm964236m1539mBm936B36m0439mBm064B32mR-39mBm906.9390.1d10:01.111htopK23;6H2423;29H36m547MtH359Mo7339mBm964e32mRi39mBmc/5.9er4.5es2:52.1473G32mapiserverf--advertise-address=144.126.131.1056--allow-privileged=truem--authorizatio24;4H39mBm88424;29H36m396Men183Mc9739mBm616/B0;1m90mSm39mBmig5.9p32.3mK1:46.64832mcilium-agentm--config-dir=/tmp/cilium/config-map39mBmKmBmh10.7er0.1au0:01.00ahtopK24;4H723224;29H36m547Met359Mc7339mBm964nB0;1m90mSr39mBmon9.6;24.5mB1:30.47332mkube-apiserver1--advertise-address=144.126.131.1058--allow-privileged=true9--authorization25;5H39mBm14025;29H36m245Mb6139mBm104e36m3839mBm3528B0;1m90mSm39mBm618.6Bm0.8930:34.89Bkube-schedulerB--authentication-kubeconfig=/etc/kubernetes/scheduler.confn--authorization-26;6H0426;29H36m547Mr.359Mh7339mBm964aB0;1m90mS039mBmm18.68;4.5436:25.14332mkube-apiserverM--advertise-address=144.126.131.105.--allow-privileged=truee--authorization27;5H39mBm06427;29H36m628M-7539mBm732v36m4039mBm948-B0;1m90mSt39mBm;27.5mB0.9720:27.9727;77H32mcontainerd39mBmK28;7H628;46HB0;1m90mSm39mBmBm7.560G1:23.3329;6H0529;30H36m45Mi6139mBm104u36m3839mBm3524B0;1m90mS.39mBm377.5-c0.8-f0:31.673G32mschedulerk--authentication-kubeconfig=/etc/kubernetes/scheduler.conf5--authorization-30;6H39mBm2530;46HB0;1m90mS/39mBmun7.560G2:49.2231;4H911231;28H32m336m269Ma4839mBm796l36m3539mBm1528B0;1m90mS239mBmu47.50H0.6710:23.8931;77H32mcilium-envoy5-c4/var/run/cilium/envoy/bootstrap-config.jsonC--base-idm0m--log-lev32;6H39mBm3932;30H36m10Mon106Md7739mBm360lB0;1m90mSg39mBm9m6.4221.3940:43.8832;75H32moperator-generic5--config-dir=/tmp/cilium/config-map --debug=false33;3H39mBm1176533;28H36m1539mBm236n36m1039mBm952r36me839mBm796aB0;1m90mS.39mBm--6.4ec0.1i20:00.27Bsshd:3root@pts/0K34;5H19234;29H32m136m.132mG536m7339mBm128936m3039mBm164uB0;1m90mS339mBmr/5.3/k0.9le4:29.57t32metcdu--advertise-client-urls=https://144.126.131.105:2379b--cert-file=/etc/kubernetes/pki/35;2H39mBm1089935;28H32m136m396M10183MB9739mBm6162B0;1m90mS/39mBmin5.3392.3K20:49.50432mcilium-agent3--config-dir=/tmp/cilium/config-map36;4H39mBm9480435m65532 0:47.36;28H32m136m271Mr6139mBm704t36m4939mBm392/B0;1m90mS339mBm:25.3i-0.8rt0:08.44e32m/corednse-conf//etc/coredns/Corefile37;6H39mBm9537;29H32m136m.132mG036m7339mBm128936m3039mBm1643B0;1m90mSa39mBmis4.3li0.9-u1:22.68p32metcd.--advertise-client-urls=https://144.126.131.105:23795--cert-file=/etc/kubernetes/pki/38;7H39mBm438;50H3.260G0:47.2539;6H0739;29H36m245M36139mBm104/36m3839mBm352tB0;1m90mSe39mBmg=3.2c/0.8er0:20.5273G32mschedul86Guthentication-kubeconfig=/etc/kubernetes/scheduler.confB--authorization-40;6H39mBm1740;29H36m269M2m109Mu5939mBm300c32mRg39mBm/t3.2ci1.4m/3:39.56m32mkube-controller-manager9--allocate-node-cidrs=truem--authentication-kubeconfig=/etc/kubern41;4H39mBm721841;28H32m136m269Mci109Mt5939mBm300eB0;1m90mS-39mBmon3.2=/1.4/k1:21.82;32mkube-controller-managerM--allocate-node-cidrs=trueS--authentication-kubeconfig=/etc/kubern42;4H39mBm7229srootdress=142;29H32m136m.132mGl36m7339mBm128=36m3039mBm164iB0;1m90mS439mBmm73.2310.9H31:24.87132metcdm--advertise-client-urls=https://144.126.131.105:2379;--cert-file=/etc/kubernetes/pki/43;2H39mBm10878743;28H32m136m396M -183Mt9739mBm616/B0;1m90mSs39mBm323.2392.3722:02.89s32mcilium-agent5--config-dir=/tmp/cilium/config-map44;2H39mBm10884444;28H32m136m396M-a183Ms9739mBm6161B0;1m90mSa39mBmpr3.2le2.3=t1:46.51u32mcilium-agentH--config-dir=/tmp/cilium/config-map45;4H39mBm91045;28H32m336m269MB4839mBm796636m3539mBm152rB0;1m90mSu39mBmoy3.2 /0.6/r0:25.4345;78H32milium-envoyo-ci/var/run/cilium/envoy/bootstrap-config.json3--base-id80M--log-lev46;4H39mBm677546;28H32m236m628M:7539mBm732i36m4039mBm948cB0;1m90mS=39mBmci2.1m/0.9fi0:20.69m32m/usr/bin/containerd39mBmK47;5H22147;30H36m69MmB109M55939mBm3000B0;1m90mSm39mBmbi2.1on1.4ne1:10.3873G32mcontroller-manager4--allocate-node-cidrs=true6--authentication-kubeconfig=/etc/kubern48;5H39mBm30848;28H32m236m124Mc9639mBm200s36m5139mBm652nB0;1m90mSr39mBmon2.1;71.2mB1:32.1048;77H32mkubelet5--bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf3--kubeconfi49;4H39mBm874149;28H32m136m310Me-106Mn7739mBm360pB0;1m90mS239mBm.12.1231.3--0:10.46l32mcilium-operator-genericH--config-dir=/tmp/cilium/config-map0--debug=false39mBmK50;82H2;16H31m||||2;74HB0;1m90m7.42;101H7109G32m43;11HB0m31m|||21GB0;1m90m	3;73H18.44;11HB0m32m|19G31m||4;74HB0;1m90m7.74;102H36m75;11HB0m32m|19GB0;1m90m 5;74H5.611;6HB0m30m46m3211;46HR	15.760G1:30.6712;5H39;49mBm20412;28H32m136m547M	 359M 7339mBm964 B0;1m90mS 39mBm  8.6  4.5  6:25.25 32mkube-apiserver --advertise-address=144.126.131.105 --allow-privileged=true --authorization13;5H39mBm30813;49H 8.660G1:32.2114;6H9714;28H32m236m124M 9639mBm200 36m5139mBm652 32mR 39mBm	7.8  1.2  1:49.81 32m/usr/bin/kubelet --bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf --kubeconfi15;5H39mBm31615;28H32m236m124M 9639mBm200 36m5139mBm652 B0;1m90mS 39mBm	7.8  1.2  0:52.58 32m/usr/bin/kubelet --bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf --kubeconfi16;5H39mBm78716;49H 7.860G2:02.9917;4H729217;28H32m236m124M 9639mBm200 36m5139mBm652 B0;1m90mS 39mBm  7.0  1.2  3:30.71 32m/usr/bin/kubelet --bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf --kubeconfi18;6H39mBm9218;29H32m136m.132mG 36m7339mBm128 36m3039mBm164 B0;1m90mS 39mBm	 6.3  0.9  4:29.65 32metcd --advertise-client-urls=https://144.126.131.105:2379 --cert-file=/etc/kubernetes/pki/19;5H39mBm19519;28H32m1136m.132mG 36m7339mBm128 36m3039mBm164 B0;1m90mS 39mBm  6.3  0.9	 1:22.76 32metcd --advertise-client-urls=https://144.126.131.105:2379 --cert-file=/etc/kubernetes/pki/20;5H39mBm32220;28H32m236m124M 9639mBm200 36m5139mBm649G 5.5  1.2	 1:41.60 32m/usr/bin/kubelet --bootstrap-kubeconfig=/etc/kubernetes/bootstrap-kubelet.conf --kubeconfi21;4H39mBm884421;28H32m136m396M  183M 9739mBm616 B0;1m90mS 39mBm	5.5  2.3  1:46.58 32mcilium-agent --config-dir=/tmp/cilium/config-map39mBmK22;4H71922;29H32m136m.132mG 36m7339mBm128 36m3039mBm164 B0;1m90mS 39mBm  4.7	 0.9  1:23.39 32metcd --advertise-client-urls=https://144.126.131.105:2379 --cert-file=/etc/kubernetes/pki/23;3H39mBm0721723;28H32m136m269M  109M 5939mBm300 B0;1m90mS 39mBm  4.7  1.4	3:39.62 32mkube-controller-manager --allocate-node-cidrs=true --authentication-kubeconfig=/etc/kubern24;6H39mBm2424;50H4.760G2:52.0825;4H865825;29H36m396M  183M 9739mBm616 B0;1m90mS 39mBm  4.7  2.3  3:29.90 32mcilium-agent --config-dir=/tmp/cilium/config-map39mBmK26;5H14026;29H36m245M 6139mBm104 36m3839mBm352 B0;1m90mS 39mBm	3.1  0.8  0:34.93 kube-scheduler --authentication-kubeconfig=/etc/kubernetes/scheduler.conf --authorization-27;5H21827;28H32m136m269M  109M 5939mBm300 B0;1m90mS 39mBm	3.1  1.4  1:21.86 32mkube-controller-manager --allocate-node-cidrs=true --authentication-kubeconfig=/etc/kubern28;4H39mBm90828;29H36m547M  359M 7339mBm950G3.1	4.5  2:38.27 32mkube-apiserver --advertise-address=144.126.131.105 --allow-privileged=true --authorization29;3H39mBm1189329;28H36m 939mBm964 36m 539mBm936 36m 439mBm064 32mR 39mBm  3.1  0.1  0:01.04 htopK
?2004h0;root@k8-0: ~root@k8-0:~# exit
logout
Connection to k8-0.v-site.net closed.
?2004hl0r3zz@tarnover:[2026-02-13 21:27:10]-$Bm
?2004hl0r3zz@tarnover:[2026-02-13 21:27:12]-$Bmexit
exit4l

Script done on 2026-02-13 21:27:16-08:00 [COMMAND_EXIT_CODE="0"]
