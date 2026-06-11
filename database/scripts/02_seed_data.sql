-- Healthcare ETL Platform - Seed Data
-- Crea usuarios iniciales y datos de demostración

-- ============================================
-- Usuarios Iniciales
-- ============================================
INSERT INTO authentication_user (
    password, is_superuser, email, full_name, document_type, document_id,
    phone, role, is_active, is_staff, date_joined
) VALUES
    -- Admin: pbkdf2_sha256$... (password: Admin123!)
    ('pbkdf2_sha256$720000$wF9KjuXrUMLrUVcFnOQvq7$V+YwxV3qVh2VHZZC5pWg0LCE/miqEghZ8EIfwFEsEAA=',
     TRUE, 'admin@healthcare-etl.com', 'Administrador Sistema', 'cc', '1000000001',
     '3001112233', 'admin', TRUE, TRUE, NOW()),

    -- Doctor (password: Doctor123!)
    ('pbkdf2_sha256$720000$wF9KjuXrUMLrUVcFnOQvq7$V+YwxV3qVh2VHZZC5pWg0LCE/miqEghZ8EIfwFEsEAA=',
     FALSE, 'doctor@healthcare-etl.com', 'Dr. Carlos Mendoza', 'cc', '1000000002',
     '3001112234', 'doctor', TRUE, FALSE, NOW()),

    -- Analista (password: Analista123!)
    ('pbkdf2_sha256$720000$wF9KjuXrUMLrUVcFnOQvq7$V+YwxV3qVh2VHZZC5pWg0LCE/miqEghZ8EIfwFEsEAA=',
     FALSE, 'analyst@healthcare-etl.com', 'Ana López García', 'cc', '1000000003',
     '3001112235', 'analyst', TRUE, FALSE, NOW());

-- Nota: La contraseña hash arriba es un placeholder. Debes generar el hash correcto
-- usando: python manage.py shell -c "from django.contrib.auth.hashers import make_password; print(make_password('Admin123!'))"

-- ============================================
-- Fuente de Datos Demo
-- ============================================
INSERT INTO etl_datasource (name, source_type, status, notes, created_at)
VALUES ('Dataset Clínico Enriquecido', 'excel', 'completed', 'Dataset generado automáticamente con ~1850 registros clínicos', NOW());
