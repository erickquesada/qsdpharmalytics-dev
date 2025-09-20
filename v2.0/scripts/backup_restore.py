"""
Script para backup e restore do PostgreSQL
Execute: 
  - python scripts/backup_restore.py backup
  - python scripts/backup_restore.py restore backup_20241215_143022.sql
"""

import sys
import os
import subprocess
from datetime import datetime
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

class DatabaseBackupRestore:
    def __init__(self):
        self.backup_dir = Path("./backups")
        self.backup_dir.mkdir(exist_ok=True)
        
        # Extrair informações da DATABASE_URL
        self.parse_database_url()
    
    def parse_database_url(self):
        """Extrair componentes da URL do banco"""
        url = settings.database_url
        
        if not url.startswith('postgresql://'):
            raise ValueError("Este script funciona apenas com PostgreSQL")
        
        # postgresql://user:password@host:port/database
        url = url.replace('postgresql://', '')
        
        if '@' in url:
            auth, host_db = url.split('@', 1)
        # The rest of the logic for parsing should go here if needed.

def create_backup(self) -> str:
    """Criar backup do banco de dados"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"pharmalitics_backup_{timestamp}.sql"
    backup_path = self.backup_dir / backup_filename
    
    print(f"🔄 Criando backup do banco de dados...")
    print(f"📁 Arquivo: {backup_path}")
    
    # Comando pg_dump
    cmd = [
        'pg_dump',
        '-h', self.host,
        '-p', self.port,
        '-U', self.user,
        '-d', self.database,
        '-f', str(backup_path),
        '--verbose',
        '--no-password'
    ]
    
    # Configurar ambiente para senha
    env = os.environ.copy()
    env['PGPASSWORD'] = self.password
    
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✅ Backup criado com sucesso!")
        print(f"📊 Tamanho: {backup_path.stat().st_size / 1024:.1f} KB")
        
        return str(backup_path)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao criar backup:")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        raise
    except FileNotFoundError:
        print("❌ pg_dump não encontrado!")
        print("Instale PostgreSQL client tools ou use Docker:")
        print("docker exec -it pharmalitics_postgres pg_dump -U pharmalitics_user pharmalitics_prod > backup.sql")
        raise

def main():
    if len(sys.argv) < 2:
        print("📚 Uso:")
        print("  python scripts/backup_restore.py backup                    # Criar backup")
        print("  python scripts/backup_restore.py restore <arquivo>        # Restaurar backup")
        print("  python scripts/backup_restore.py list                     # Listar backups")
        print("  python scripts/backup_restore.py cleanup                  # Limpar backups antigos")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    
    try:
        backup_restore = DatabaseBackupRestore()
        
        if action == 'backup':
            backup_file = backup_restore.create_backup()
            print(f"\n🎉 Backup salvo em: {backup_file}")
        
        elif action == 'restore':
            if len(sys.argv) < 3:
                print("❌ Especifique o arquivo de backup para restaurar")
                backup_restore.list_backups()
                sys.exit(1)
            
            backup_file = sys.argv[2]
            success = backup_restore.restore_backup(backup_file)
            
            # Adicione o tratamento do resultado do restore aqui
            if success:
                print(f"\n🎉 Restore concluído com sucesso!")
            else:
                print(f"\n❌ Falha no restore do backup!")
                sys.exit(1)
        
        elif action == 'list':
            backup_restore.list_backups()
        
        elif action == 'cleanup':
            keep_count = 10
            if len(sys.argv) >= 3:
                try:
                    keep_count = int(sys.argv[2])
                except ValueError:
                    print("❌ Número de backups a manter deve ser um inteiro")
                    sys.exit(1)
            
            backup_restore.cleanup_old_backups(keep_count)
        
        else:
            print(f"❌ Ação desconhecida: {action}")
            print("Ações disponíveis: backup, restore, list, cleanup")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Erro: {e}")
        sys.exit(1)