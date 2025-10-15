#!/bin/bash
set -e

echo "🔧 Initializing QSD Pharmalytics..."

echo ""
echo "📊 Waiting for PostgreSQL..."
max_retries=30
retry_count=0
while ! pg_isready -h postgres -U ${POSTGRES_USER:-pharmalitics_user} > /dev/null 2>&1; do
  retry_count=$((retry_count + 1))
  if [ $retry_count -ge $max_retries ]; then
    echo "❌ PostgreSQL failed to become ready after ${max_retries} attempts"
    exit 1
  fi
  sleep 1
done
echo "✅ PostgreSQL is ready!"

echo "🔄 Running database migrations..."
cd /app
if alembic upgrade head; then
  echo "✅ Migrations completed successfully!"
else
  echo "⚠️  Migrations skipped or failed - continuing startup"
fi

echo "👤 Creating initial admin user..."
python3 -c "
import sys
sys.path.insert(0, '/app')

try:
    from backend.core.database import SessionLocal
    from backend.models.user import User
    from backend.core.security import get_password_hash

    db = SessionLocal()
    try:
        # Check if admin exists
        admin = db.query(User).filter(User.username == 'admin').first()
        if not admin:
            admin = User(
                email='admin@qsdpharma.com',
                username='admin',
                hashed_password=get_password_hash('admin123'),
                first_name='Admin',
                last_name='System',
                role='admin',
                is_active=True
            )
            db.add(admin)
            db.commit()
            print('✅ Admin user created successfully!')
        else:
            print('ℹ️  Admin user already exists')
    except Exception as e:
        print(f'⚠️  Error creating admin user: {e}')
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
except Exception as e:
    print(f'❌ Could not create admin user: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "🚀 Starting application..."
exec "$@"
