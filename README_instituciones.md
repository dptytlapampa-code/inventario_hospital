# Instituciones - Migración y Seed desde CSV

Este cambio introduce el modelo base `Institucion`, migra las relaciones existentes y agrega un script de seed para poblar la base con datos oficiales a partir de `Contenido.csv`.

## Migraciones

```bash
alembic upgrade head
```

> Si necesitás generar una nueva revisión sobre estos cambios:
>
> ```bash
> alembic revision --autogenerate -m "add institucion model and relations"
> alembic upgrade head
> ```

## Seed desde CSV

```bash
python scripts/seed_instituciones.py --csv ./Contenido.csv
```

El script puede ejecutarse múltiples veces. Es idempotente: actualiza registros existentes y crea servicios/oficinas predeterminados solo si no existen.

### Ejemplo de salida

```
INFO Cargando datos desde /ruta/al/Contenido.csv
Instituciones: 100%|████████████████████████████████████████| 130/130 [00:03<00:00, 39.55inst./s]
INFO Proceso completado. Instituciones creadas=128, actualizadas=2, omitidas=0, servicios creados=384, oficinas creadas=896.
```

### Notas

* Todos los registros del CSV se normalizan al formato `Hospital <Nombre> - <Localidad>`.
* La columna `tipo_institucion` se fija en `Hospital` para esta iteración.
* Los servicios creados automáticamente son Administración, Consultorios y Guardia; cada uno genera sus oficinas por defecto.
* Las ejecuciones posteriores reutilizan los mismos registros y evitan duplicados.
