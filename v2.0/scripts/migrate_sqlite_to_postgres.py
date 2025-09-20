"""
Script para migrar dados do SQLite para PostgreSQL
Execute: python scripts/migrate_sqlite_to_postgres.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
from app.core.config import settings

def migrate_sqlite_to_postgres():
    """Migrar dados do SQLite para PostgreSQL"""
    
    # URLs dos bancos
    sqlite_url = "sqlite:///./pharmalitics.db"
    postgres_url = settings.database_url
    
    print("🔄 Iniciando migração SQLite → PostgreSQL")
    print(f"📤 Origem: {sqlite_url}")
    print(f"📥 Destino: {postgres_url}")
    
    try:
        # Conectar aos bancos
        sqlite_engine = create_engine(sqlite_url)
        postgres_engine = create_engine(postgres_url)
        
        print("✅ Conexões estabelecidas")
        
        # Lista de tabelas para migrar
        tables_to_migrate = [
            'products',
            'pharmacies', 
            'sales',
            'kpis',
            'kpi_values',
            'analytics_cache',
            'alerts',
            'dashboards',
            'report_templates',
            'data_sources'
        ]
        
        migration_summary = {}
        
        for table in tables_to_migrate:
            try:
                print(f"\n📋 Migrando tabela: {table}")
                
                # Verificar se tabela existe no SQLite
                result = sqlite_engine.execute(
                    text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                    {"table_name": table}
                )
                
                if not result.fetchone():
                    print(f"⚠️  Tabela {table} não existe no SQLite, pulando...")
                    migration_summary[table] = {"status": "skipped", "reason": "table_not_exists"}
                    continue
                
                # Ler dados do SQLite
                df = pd.read_sql_table(table, sqlite_engine)
                
                if df.empty:
                    print(f"⚠️  Tabela {table} está vazia, pulando...")
                    migration_summary[table] = {"status": "skipped", "reason": "empty_table"}
                    continue
                
                print(f"📊 Encontrados {len(df)} registros")
                
                # Verificar e criar tabela no PostgreSQL se necessário
                with postgres_engine.connect() as conn:
                    # Verificar se tabela existe
                    exists_result = conn.execute(text("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = :table_name
                        );
                    """), {"table_name": table})
                    
                    table_exists = exists_result.scalar()
                
                if table_exists:
                    print(f"📝 Tabela {table} já existe no PostgreSQL")
                    
                    # Verificar se já tem dados
                    existing_count = pd.read_sql(
                        f"SELECT COUNT(*) as count FROM {table}",
                        postgres_engine
                    )['count'].iloc[0]
                    
                    if existing_count > 0:
                        print(f"⚠️  Tabela {table} já tem {existing_count} registros")
                        choice = input("Deseja sobrescrever? (y/N): ").lower()
                        
                        if choice != 'y':
                            print(f"⏭️  Pulando tabela {table}")
                            migration_summary[table] = {
                                "status": "skipped", 
                                "reason": "user_choice",
                                "existing_records": existing_count
                            }
                            continue
                        else:
                            # Limpar tabela
                            with postgres_engine.connect() as conn:
                                conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
                                conn.commit()
                            print(f"🗑️  Tabela {table} limpa")
                else:
                    print(f"⚠️  Tabela {table} não existe no PostgreSQL")
                    print("Execute as migrations primeiro: alembic upgrade head")
                    migration_summary[table] = {"status": "failed", "reason": "table_not_exists_postgres"}
                    continue
                
                # Migrar dados
                try:
                    df.to_sql(
                        table, 
                        postgres_engine, 
                        if_exists='append',
                        index=False,
                        method='multi',
                        chunksize=1000
                    )
                    
                    # Verificar se migração foi bem sucedida
                    final_count = pd.read_sql(
                        f"SELECT COUNT(*) as count FROM {table}",
                        postgres_engine
                    )['count'].iloc[0]
                    
                    print(f"✅ Migração concluída: {final_count} registros")
                    
                    migration_summary[table] = {
                        "status": "success",
                        "records_migrated": final_count,
                        "source_records": len(df)
                    }
                    
                    # Resetar sequences no PostgreSQL
                    with postgres_engine.connect() as conn:
                        try:
                            # Obter nome da sequence
                            sequence_result = conn.execute(text(f"""
                                SELECT pg_get_serial_sequence('{table}', 'id') as sequence_name
                            """))
                            
                            sequence_name = sequence_result.scalar()
                            
                            if sequence_name:
                                # Resetar sequence para o próximo valor
                                conn.execute(text(f"""
                                    SELECT setval('{sequence_name}', 
                                        COALESCE((SELECT MAX(id) FROM {table}), 0) + 1, 
                                        false)
                                """))
                                conn.commit()
                                print(f"🔄 Sequence {sequence_name} resetada")
                        except Exception as seq_error:
                            print(f"⚠️  Erro ao resetar sequence: {seq_error}")
                
                except Exception as migration_error:
                    print(f"❌ Erro na migração da tabela {table}: {migration_error}")
                    migration_summary[table] = {
                        "status": "failed",
                        "error": str(migration_error)
                    }
            
            except Exception as table_error:
                print(f"❌ Erro ao processar tabela {table}: {table_error}")
                migration_summary[table] = {
                    "status": "failed",
                    "error": str(table_error)
                }
        
        # Relatório final
        print("\n" + "="*50)
        print("📊 RELATÓRIO DE MIGRAÇÃO")
        print("="*50)
        
        successful = 0
        failed = 0
        skipped = 0
        total_records = 0
        
        for table, info in migration_summary.items():
            status = info['status']
            
            if status == 'success':
                successful += 1
                records = info.get('records_migrated', 0)
                total_records += records
                print(f"✅ {table:<20} - {records:>6} registros migrados")
            
            elif status == 'failed':
                failed += 1
                error = info.get('error', 'Erro desconhecido')
                print(f"❌ {table:<20} - FALHA: {error}")
            
            elif status == 'skipped':
                skipped += 1
                reason = info.get('reason', 'Motivo desconhecido')
                print(f"⏭️  {table:<20} - PULADA: {reason}")
        
        print("-"*50)
        print(f"✅ Tabelas migradas com sucesso: {successful}")
        print(f"❌ Tabelas com falha: {failed}")
        print(f"⏭️  Tabelas puladas: {skipped}")
        print(f"📊 Total de registros migrados: {total_records}")
        print(f"🕒 Migração concluída em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        
        if failed == 0:
            print("\n🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("Agora você pode usar o PostgreSQL como banco principal.")
            print("Altere DATABASE_URL no .env para apontar para PostgreSQL.")
        else:
            print(f"\n⚠️  MIGRAÇÃO CONCLUÍDA COM {failed} ERRO(S)")
            print("Verifique os erros acima e execute novamente se necessário.")
        
    except Exception as e:
        print(f"❌ Erro crítico na migração: {e}")
        return False
    
    finally:
        # Fechar conexões
        try:
            sqlite_engine.dispose()
            postgres_engine.dispose()
        except:
            pass
    
    return successful > 0 and failed == 0

if __name__ == "__main__":
    print("🚀 QSDPharmalitics - Migração de Dados")
    print("SQLite → PostgreSQL")
    print("-" * 50)
    
    # Verificar se .env está configurado para PostgreSQL
    if "postgresql://" not in settings.database_url:
        print("❌ DATABASE_URL não está configurada para PostgreSQL!")
        print("Configure DATABASE_URL no .env antes de executar a migração.")
        sys.exit(1)
    
    # Confirmação do usuário
    print(f"🎯 Banco de destino: {settings.database_url}")
    confirm = input("\nDeseja continuar com a migração? (y/N): ").lower()
    
    if confirm != 'y':
        print("❌ Migração cancelada pelo usuário.")
        sys.exit(0)
    
    # Executar migração
    success = migrate_sqlite_to_postgres()
    
    if success:
        print("\n✅ Processo finalizado com sucesso!")
        sys.exit(0)
    else:
        print("\n❌ Processo finalizado com erros!")
        sys.exit(1)