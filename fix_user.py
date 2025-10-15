#!/usr/bin/env python3
import sys
sys.path.insert(0, '/app')

from backend.core.database import SessionLocal
from backend.models.user import User
from backend.core.security import get_password_hash, verify_password

def fix_user(email, password):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ Usuário {email} não encontrado")
            print("\nUsuários no banco:")
            users = db.query(User).all()
            for u in users:
                print(f"  - {u.email} (username: {u.username})")
            return False
        
        print(f"✅ Usuário encontrado: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Ativo: {user.is_active}")
        print(f"   Verificado: {user.is_verified}")
        
        # Testar senha atual
        if verify_password(password, user.hashed_password):
            print(f"✅ Senha já está correta!")
            return True
        
        # Atualizar senha
        user.hashed_password = get_password_hash(password)
        user.is_active = True
        user.is_verified = True
        db.commit()
        
        print(f"✅ Senha atualizada com sucesso!")
        
        # Testar nova senha
        db.refresh(user)
        if verify_password(password, user.hashed_password):
            print(f"✅ Verificação: Senha funcionando!")
            return True
        else:
            print(f"❌ Erro: Senha não está funcionando após atualização")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    email = "erickquesada2005@gmail.com"
    password = "quesada123"
    
    print(f"🔧 Corrigindo usuário: {email}")
    print(f"   Senha: {password}")
    print()
    
    if fix_user(email, password):
        print()
        print("=" * 50)
        print("✅ SUCESSO! Você pode fazer login agora com:")
        print(f"   Email: {email}")
        print(f"   Senha: {password}")
        print("=" * 50)
    else:
        print()
        print("❌ Falhou. Verifique os erros acima.")
