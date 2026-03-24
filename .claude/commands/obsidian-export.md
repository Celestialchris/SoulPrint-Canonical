Export canonical ledger to Obsidian vault.
Usage: /project:obsidian-export

Run: python -m src.obsidian.cli export --db instance/soulprint.db --vault $ARGUMENTS
If no argument given, use C:\Users\chr\SoulPrint-Vault as default.
After export, report counts and remind to open vault in Obsidian.
