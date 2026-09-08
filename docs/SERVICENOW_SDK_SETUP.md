# Guía de configuración del SDK de ServiceNow en Kiro

Guía paso a paso para dejar operativo el **ServiceNow SDK** (`@servicenow/sdk`, CLI `now-sdk`) dentro de Kiro / VS Code en Windows, autenticar contra las instancias de Amrize (QUAL y PRD) y consultar datos en vivo (incidents, changes, RITM, problems, etc.).

> Validado en Windows con PowerShell. Todos los comandos se ejecutan en una terminal PowerShell.

---

## 1. Contexto: qué es y qué NO es

- ServiceNow aquí funciona a través del **power `servicenow-sdk`**, que envuelve el CLI `@servicenow/sdk` (`now-sdk`). **No es un servidor MCP.**
- El CLI se opera por línea de comandos; Kiro puede ejecutar esos comandos por ti.
- Capacidades principales:
  - **`now-sdk query`** — consulta de datos en vivo (SOLO LECTURA) sobre cualquier tabla.
  - **`now-sdk explain`** — documentación integrada (cientos de topics).
  - **`now-sdk auth`** — gestión de autenticación por instancia.
  - Comandos de desarrollo de apps Fluent (`init`, `build`, `install`, etc.) — no necesarios para solo consultar.

### Limitaciones importantes (confirmadas)

| Capacidad | ¿Disponible con el SDK? |
|-----------|-------------------------|
| Consultar registros (incident, change, RITM, problem...) | ✅ Sí (`query`, solo lectura) |
| Listar adjuntos de un registro | ✅ Sí (`query` sobre `sys_attachment`) |
| **Crear** un change request u otro registro de negocio | ❌ No con `now-sdk`. Requiere Table API REST (`POST`). |
| **Modificar / avanzar estados** de un registro | ❌ No con `now-sdk`. Requiere Table API REST (`PATCH`). |
| Descargar el binario de un adjunto | ❌ No con `now-sdk`. Requiere Attachment API REST (`GET .../file`). |
| Leer metadatos `sys_dictionary` / `sys_choice` | ⚠️ Depende de permisos del usuario (a menudo restringidos). |

> Para crear/modificar registros o descargar adjuntos se usa la **REST API de ServiceNow** con la misma autenticación básica (ver sección 8).

---

## 2. Requisito previo: Node.js

El CLI corre sobre Node.js. Si `node`/`npm`/`npx` no están instalados:

### Opción recomendada (sin permisos de administrador)

Instalación portable de Node en el perfil del usuario:

```powershell
$ver = 'v24.19.0'
$dir = "$env:USERPROFILE\nodejs"
$zip = "$env:TEMP\node-$ver-win-x64.zip"
$url = "https://nodejs.org/dist/$ver/node-$ver-win-x64.zip"
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
if (Test-Path $dir) { Remove-Item -Recurse -Force $dir }
Expand-Archive -Path $zip -DestinationPath $env:USERPROFILE -Force
Rename-Item "$env:USERPROFILE\node-$ver-win-x64" $dir
```

Añadir Node al PATH de usuario (persistente):

```powershell
$dir = "$env:USERPROFILE\nodejs"
$userPath = [Environment]::GetEnvironmentVariable('Path','User')
if ($userPath -notlike "*$dir*") {
    [Environment]::SetEnvironmentVariable('Path', "$userPath;$dir", 'User')
}
```

> Nota: el instalador MSI oficial (`winget install OpenJS.NodeJS.LTS`) requiere elevación de administrador (UAC) y puede fallar con código 1603 en entornos corporativos. La instalación portable de arriba lo evita.

### Verificar

Abre una **terminal nueva** (para que tome el PATH actualizado) y comprueba:

```powershell
node --version   # -> v24.19.0
npm --version    # -> 11.17.0
```

---

## 3. Cargar el PATH en cada terminal

El PATH de usuario solo aplica a terminales **nuevas**. Si `now-sdk` no se reconoce, carga el PATH manualmente al inicio de la sesión:

```powershell
$env:Path = "$env:USERPROFILE\nodejs;$env:USERPROFILE\nodejs\node_modules\npm\bin;$env:Path"
```

> Tip: guarda esta línea a mano; hay que ejecutarla una vez por cada terminal nueva (o añadirla a tu perfil de PowerShell).

---

## 4. Instalar el SDK de ServiceNow

Instalación global (una sola vez; deja el comando `now-sdk` disponible y cacheado):

```powershell
$env:Path = "$env:USERPROFILE\nodejs;$env:Path"
npm install -g @servicenow/sdk@latest
```

La instalación descarga ~500 paquetes y tarda un par de minutos. Verificar:

```powershell
now-sdk --version   # -> 4.11.2 (o superior)
now-sdk --help
```

> Requisitos de versión: `explain` necesita >= 4.6.0; `query` necesita >= 4.8.0.

---

## 5. Autenticación

### Métodos disponibles

- **basic** — usuario + contraseña. Simple. Ideal para usuarios de servicio / integración.
- **oauth** — flujo por navegador (code grant). Necesario para SSO, pero requiere que la instancia tenga un **OAuth API endpoint for external clients** registrado (Client ID/Secret/Redirect URL).

### Nota sobre SSO corporativo

Si tu instancia usa **SSO puro**:
- `basic` con tu usuario personal normalmente **falla** (tu contraseña vive en el proveedor de identidad, no en ServiceNow).
- `oauth` es la vía correcta, pero si no hay OAuth client registrado, el navegador muestra **"Security constraints prevent access to requested page"**.
- **Solución práctica:** usar un **usuario de integración/servicio** con login local en ServiceNow (contraseña propia, no SSO) y permisos de lectura API → autenticar con `basic`.

### Comando de login (basic)

```powershell
now-sdk auth --add https://TU-INSTANCIA.service-now.com --type basic --alias TU-ALIAS
```

El comando pide alias, usuario y contraseña (la contraseña se introduce en el prompt, no queda en el historial). Las credenciales se guardan cifradas en `.now-sdk/` (gitignored).

### Ejemplos reales (Amrize)

```powershell
# QUAL (pruebas)
now-sdk auth --add https://oneservicequalna.service-now.com --type basic --alias oneservicequalna

# PRD (producción) — usar un usuario de integración
now-sdk auth --add https://oneservicena.service-now.com --type basic --alias oneservicena-prd
```

> **Convención de alias:** usar alias claros y distintos por entorno (`oneservicequalna`, `oneservicena-prd`) para no confundir QUAL con PRD.

### Gestión de credenciales

```powershell
now-sdk auth --list                 # listar credenciales guardadas (* = default)
now-sdk auth --use TU-ALIAS         # fijar cual es la default
now-sdk auth --delete TU-ALIAS      # borrar unas credenciales
```

---

## 6. Consultar datos (`now-sdk query`)

### Sintaxis base

```powershell
now-sdk query <tabla> -q '<encoded_query>' -o json
```

### Flags útiles

| Flag | Descripción |
|------|-------------|
| `-q, --query` | Filtro (encoded query). **Requerido.** Ej: `active=true^priority<=2` |
| `-f, --fields` | Campos a devolver (coma-separados) |
| `--limit` | Máx. registros por página (default 100) |
| `--display-value all` | Devuelve valor crudo + etiqueta (útil para estados) |
| `-a, --auth` | **Alias de credenciales a usar (elige el entorno).** Ej: `-a oneservicena-prd` |
| `-o, --output` | `json` para salida estructurada |
| `-s, --select` | Extraer un campo puntual (ej. `records[0].sys_id`) |

> **Buena práctica:** en PRD, incluye SIEMPRE `-a <alias-prd>` explícito para saber contra qué entorno consultas.

### Tablas frecuentes

| Tabla | Contenido |
|-------|-----------|
| `incident` | Incidentes |
| `change_request` | Changes |
| `sc_req_item` | RITM (Requested Items) |
| `sc_request` | Requests (REQ) |
| `problem` | Problemas (PRB) |
| `sys_user` | Usuarios |
| `sys_attachment` | Adjuntos de cualquier registro |

### Ejemplos

```powershell
$env:Path = "$env:USERPROFILE\nodejs;$env:Path"

# Incidents activos de prioridad alta
now-sdk query incident -q 'active=true^priority<=2' -f 'number,short_description,state' -a oneservicena-prd -o json

# Buscar un usuario por nombre (para obtener su sys_id)
now-sdk query sys_user -q 'nameLIKEhernandez' -f 'sys_id,user_name,name,email' -a oneservicena-prd -o json

# Incidentes de un usuario (por sys_id) en varios roles
now-sdk query incident -q 'caller_id=<sys_id>^ORassigned_to=<sys_id>^ORopened_by=<sys_id>' -f 'number,short_description,state' -a oneservicena-prd --display-value all -o json

# Incidentes abiertos de un grupo de asignacion
now-sdk query incident -q 'assignment_group=<sys_id>^active=true' -f 'number,short_description,state,assigned_to' -a oneservicena-prd --display-value all -o json

# Detalle completo de un ticket
now-sdk query incident -q 'number=INC08340528' -f 'number,short_description,description,state,priority,caller_id,assigned_to,assignment_group,opened_at,comments,work_notes' -a oneservicena-prd --display-value all -o json

# Adjuntos de un incident
now-sdk query sys_attachment -q 'table_name=incident^table_sys_id=<sys_id_incident>' -f 'sys_id,file_name,content_type,size_bytes' -a oneservicena-prd --display-value all -o json
```

### Operadores de encoded query (referencia rápida)

- `^` = AND · `^OR` = OR
- `=` igual · `!=` distinto · `LIKE` contiene · `STARTSWITH` · `IN`
- `<=` `>=` para números/prioridades
- `ORDERBY<campo>` / `ORDERBYDESC<campo>`
- Valores dinámicos: `javascript:gs.getUserID()` (usuario actual), `javascript:gs.beginningOfToday()`

Documentación completa:
```powershell
now-sdk explain encoded-query-guide --format=raw
```

---

## 7. Documentación integrada (`now-sdk explain`)

```powershell
now-sdk explain --list --format=raw                 # todos los topics
now-sdk explain <topic> --list --peek --format=raw  # buscar y previsualizar
now-sdk explain <topic> --peek --format=raw         # preview de un topic
now-sdk explain <topic> --format=raw                # topic completo
```

> Consejo: usa siempre `--peek` antes de abrir un topic completo para no gastar contexto.

---

## 8. Operaciones de escritura y adjuntos (REST API)

El SDK `now-sdk` NO crea/modifica registros ni descarga adjuntos. Para eso se usa la **REST API de ServiceNow** con la misma autenticación básica.

### Crear un registro (ej. change request)

```
POST https://TU-INSTANCIA.service-now.com/api/now/table/change_request
Body JSON: { "short_description": "...", "type": "Normal Minor", ... }
```

### Modificar / avanzar estado

```
PATCH https://TU-INSTANCIA.service-now.com/api/now/table/change_request/{sys_id}
Body JSON: { "state": "<codigo>" }
```

> Ojo: los modelos de estado pueden ser personalizados y estar gobernados por business rules / flujos de aprobación (CAB). Un salto directo de estado puede ser rechazado o dejar el registro inconsistente. Validar en QUAL primero.

### Descargar el binario de un adjunto

```
GET https://TU-INSTANCIA.service-now.com/api/now/attachment/{sys_id}/file
```

### Script incluido: leer/extraer adjuntos

Se incluye `tools/snow_read_attachment.py` que lista adjuntos, los descarga y extrae el texto de archivos `.docx` (solo con librería estándar, sin dependencias externas).

Credenciales por variables de entorno (NUNCA en el código):

```powershell
$env:SNOW_INSTANCE = "https://oneservicena.service-now.com"
$env:SNOW_USER     = "tu_usuario_integracion"
$env:SNOW_PASS     = "********"

python tools\snow_read_attachment.py --number INC08340528 --list
python tools\snow_read_attachment.py --number INC08340528 --extract-docx
python tools\snow_read_attachment.py --number INC08340528 --download-all
python tools\snow_read_attachment.py --table change_request --number CHG0435576 --extract-docx
```

> Las variables `$env:` definidas en una terminal solo viven en esa sesión. Para que otro proceso las vea, usar `[Environment]::SetEnvironmentVariable("SNOW_PASS","...","User")` y **borrarlas al terminar** con el mismo comando pasando `$null`.

---

## 8b. MCP Server "Service Now" (alternativa nativa en Kiro)

Además del CLI `now-sdk`, el workspace incluye un **MCP server propio** que expone ServiceNow como tools nativas dentro de Kiro. Ventajas frente al CLI: no depende de descargas de npx, evita los "cortes" de comando, y **soporta escritura** (crear/actualizar registros, avanzar estados, work notes) y **adjuntos** (listar y extraer texto de `.docx`) — cosas que el `now-sdk query` (solo lectura) no cubre.

### Archivos del servidor

| Archivo | Rol |
|---------|-----|
| `servicenow_client.py` | Cliente REST (Table API + Attachment API), basic auth, lectura y escritura. |
| `servicenow_server.py` | MCP server data-driven (stdio), define las tools. Config por variables de entorno. |

Requisitos: Python 3.10+ y los paquetes `mcp` y `requests` (ver `requirements.txt`).

### Tools disponibles

**Lectura:**
- `snow_ping` — verifica conexión.
- `snow_query` — consulta cualquier tabla (encoded query, campos, paging, display value).
- `snow_get_record` — un registro completo por número (INC/CHG/RITM/PRB).
- `snow_find_user` — busca usuario por nombre/username/email → devuelve sys_id.
- `snow_list_attachments` — lista adjuntos de un registro.
- `snow_extract_docx` — descarga y extrae el texto de un `.docx` adjunto.

**Escritura** (no disponible vía `now-sdk`):
- `snow_create_record` — crea registros (ej. change_request).
- `snow_update_record` — actualiza campos por número.
- `snow_advance_state` — avanza el estado de un change (state code).
- `snow_add_work_note` — añade work note / comentario.

### Configuración en `.kiro/settings/mcp.json`

El servidor lee la conexión de variables de entorno: `SNOW_INSTANCE`, `SNOW_USER`, `SNOW_PASSWORD`, `SNOW_ENV`. Se registran **dos entradas** (una por entorno) para poder apuntar a PRD o QUAL de forma aislada.

**Entrada PRD:**

```json
"Service Now": {
  "command": "C:\\Users\\<usuario>\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
  "args": ["C:\\Users\\<usuario>\\ANDRES-WORKSPACE\\servicenow_server.py"],
  "cwd": "C:\\Users\\<usuario>\\ANDRES-WORKSPACE",
  "env": {
    "SNOW_INSTANCE": "https://oneservicena.service-now.com",
    "SNOW_USER": "kiro_integration",
    "SNOW_PASSWORD": "PON_AQUI_LA_CLAVE",
    "SNOW_ENV": "PRD"
  },
  "disabled": false,
  "autoApprove": [
    "snow_ping", "snow_query", "snow_get_record",
    "snow_find_user", "snow_list_attachments", "snow_extract_docx"
  ]
}
```

**Entrada QUAL:**

```json
"Service Now QUAL": {
  "command": "C:\\Users\\<usuario>\\AppData\\Local\\Programs\\Python\\Python312\\python.exe",
  "args": ["C:\\Users\\<usuario>\\ANDRES-WORKSPACE\\servicenow_server.py"],
  "cwd": "C:\\Users\\<usuario>\\ANDRES-WORKSPACE",
  "env": {
    "SNOW_INSTANCE": "https://oneservicequalna.service-now.com",
    "SNOW_USER": "test_kiro",
    "SNOW_PASSWORD": "PON_AQUI_LA_CLAVE",
    "SNOW_ENV": "QUAL"
  },
  "disabled": false,
  "autoApprove": [
    "snow_ping", "snow_query", "snow_get_record",
    "snow_find_user", "snow_list_attachments", "snow_extract_docx",
    "snow_create_record", "snow_update_record", "snow_advance_state", "snow_add_work_note"
  ]
}
```

### Notas de seguridad y convención

- **`autoApprove` por entorno, a propósito:**
  - **PRD** → solo tools de **lectura** en auto-aprobación. Las de escritura piden confirmación manual (evita modificar producción por accidente).
  - **QUAL** → incluye también las tools de **escritura**, porque es el entorno de pruebas donde sí queremos crear/avanzar changes.
- **`SNOW_PASSWORD` queda en texto plano** en `mcp.json` (igual que las credenciales SAP). Ese archivo **no debe subirse a git**.
- El label `SNOW_ENV` aparece en los mensajes de las tools, así siempre se sabe contra qué entorno se opera.
- **El archivo `.kiro/settings/mcp.json` está protegido**: Kiro no puede editarlo automáticamente; hay que actualizarlo a mano.
- Tras guardar el `mcp.json`, reconectar los servers desde la vista MCP de Kiro (o reiniciar).

### Uso rápido (una vez conectado)

- Probar conexión: tool `snow_ping`.
- Consultar: `snow_query` con `table=incident`, `query=active=true^priority<=2`.
- Crear un change de prueba (solo QUAL): `snow_create_record` con `table=change_request` y un objeto `fields`.
- Avanzar estado (solo QUAL): `snow_advance_state` con `number=CHG...` y `state=<código>` (ver modelo de estados en la sección 6 / datos reales).

---

## 9. Solución de problemas (troubleshooting)

| Síntoma | Causa / Solución |
|---------|------------------|
| `npx`/`node`/`now-sdk` no se reconoce | El PATH no está cargado en esta terminal. Ejecuta la línea de la sección 3, o abre una terminal nueva. |
| MSI de Node falla con código 1603 | Requiere admin (UAC). Usa la instalación portable de la sección 2. |
| `auth --list` dice "No credentials found" | El login no se guardó. En OAuth suele ser por falta de OAuth client (ver "Security constraints"). Usar basic con usuario de servicio. |
| Navegador muestra "Security constraints prevent access" | OAuth sin client registrado en la instancia. Usar basic, o pedir registro de OAuth endpoint. |
| Login basic falla con usuario SSO | Tu usuario es solo-SSO. Necesitas un usuario de integración con login local. |
| Una query devuelve `records: []` inesperadamente | Probable falta de ACL de lectura del usuario sobre esa tabla (ej. `sc_req_item`, `sys_dictionary`, `sys_choice`). Pedir el permiso o usar otro usuario. |
| Un comando "se corta" sin salida | Comando aún ejecutándose (primera descarga de npx, etc.). Reintentar; una vez cacheado responde rápido. |

---

## 10. Checklist rápido para un usuario nuevo

1. [ ] Instalar Node.js (portable, sección 2) y verificar `node --version`.
2. [ ] Cargar el PATH en la terminal (sección 3).
3. [ ] `npm install -g @servicenow/sdk@latest` y verificar `now-sdk --version`.
4. [ ] Conseguir credenciales:
   - QUAL: usuario de pruebas.
   - PRD: **usuario de integración** con login local + permisos de lectura API.
5. [ ] `now-sdk auth --add <url> --type basic --alias <alias>` para cada entorno.
6. [ ] `now-sdk auth --list` para confirmar.
7. [ ] Probar: `now-sdk query incident -q 'active=true' --limit 3 -f 'number,short_description,state' -a <alias> -o json`.
8. [ ] (Opcional) Para adjuntos/escritura: usar la REST API / el script `tools/snow_read_attachment.py`.
9. [ ] (Alternativa nativa) Configurar el **MCP server "Service Now"** en `mcp.json` (sección 8b) — da tools de lectura, escritura y adjuntos dentro de Kiro sin usar el CLI.

---

## Referencias

- Entornos Amrize:
  - QUAL: `https://oneservicequalna.service-now.com` (alias sugerido: `oneservicequalna`)
  - PRD: `https://oneservicena.service-now.com` (alias sugerido: `oneservicena-prd`)
- Documentación oficial del SDK: `now-sdk explain <topic> --format=raw`
- Landing oficial: https://docs.servicenow.com/csh?topicname=servicenow-sdk-landing.html
