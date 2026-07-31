<p align="center">
  <img src="../assets/session-alarm-logo.svg" width="176" alt="Logotipo de Session Alarm">
</p>

<h1 align="center">Session Alarm</h1>

<p align="center">
  <strong>Deja de vigilar constantemente a tus agentes de programación.</strong><br>
  Escucha un animal cuando Codex o Claude Code necesite tu atención.
</p>

<p align="center">
  <a href="https://github.com/djfksjd/session-alarm/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/djfksjd/session-alarm/ci.yml?branch=main&style=flat-square&label=CI"></a>
  <a href="../LICENSE"><img alt="Licencia MIT" src="https://img.shields.io/badge/licencia-MIT-2EC4B6?style=flat-square"></a>
  <img alt="Python 3.9+" src="https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white">
  <img alt="12 sonidos" src="https://img.shields.io/badge/animales_reales-12-FFB703?style=flat-square">
</p>

<p align="center">
  <a href="../README.md">English</a> ·
  <a href="README.ko.md">한국어</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.zh-CN.md">简体中文</a> · Español
</p>

---

Session Alarm es un plugin de notificaciones mediante hooks creado específicamente para
**Codex y Claude Code**. Reproduce un sonido y, opcionalmente, muestra una notificación de
escritorio cuando el agente necesita una respuesta, termina un turno, se detiene por un error o
cierra una sesión.

Los 12 sonidos integrados son grabaciones breves de animales reales. Cada página individual de
Freesound indicaba CC0 1.0 Universal al recuperarse; el manifiesto registra la página exacta, el
autor y los SHA-256 de la vista previa pública y del WAV procesado. También puedes añadir un WAV
propio o con licencia.

<table>
  <tr>
    <td width="25%" align="center"><strong>🔔 Determinista</strong><br>Los hooks del ciclo de vida funcionan sin depender de la memoria del modelo.</td>
    <td width="25%" align="center"><strong>🐈 12 animales</strong><br>Elige una grabación real o añade tu propio WAV.</td>
    <td width="25%" align="center"><strong>🛡️ Licencia verificada</strong><br>Condiciones comerciales, origen, fecha y sumas de verificación documentadas.</td>
    <td width="25%" align="center"><strong>🏠 Solo local</strong><br>Sin cuenta, servidor, análisis, telemetría ni solicitudes de red.</td>
  </tr>
</table>

## Cuándo suena

| Evento | Codex | Claude Code | Predeterminado |
|---|---|---|---|
| Necesita respuesta | Solicitud de permiso o respuesta que termina en pregunta | Permiso, diálogo, agente en segundo plano o pregunta | Gato |
| Trabajo terminado | Fin de la respuesta actual | Fin de respuesta o agente en segundo plano terminado | Gallo |
| Error | Evento de error disponible | `StopFailure` | Cuervo |
| Fin de sesión | `SessionEnd` | `SessionEnd` | Búho |

> [!NOTE]
> “Trabajo terminado” significa que el agente terminó su turno actual. El sonido de finalización se
> omite si todavía hay tareas conocidas en segundo plano o programaciones de sesión activas.

## Instalación

### Codex

```bash
codex plugin marketplace add djfksjd/session-alarm
codex plugin add session-alarm@session-alarm
```

Inicia un hilo nuevo, abre `/hooks`, revisa los comandos y confía en los hooks de Session Alarm.
Para configurar en cualquier momento:

```text
$session-alarm
```

### Claude Code

```bash
claude plugin marketplace add djfksjd/session-alarm
claude plugin install session-alarm@session-alarm
```

Inicia una sesión nueva o ejecuta `/reload-plugins` y configura:

```text
/session-alarm:session-alarm
```

### Ejecución local

```bash
git clone https://github.com/djfksjd/session-alarm.git
cd session-alarm
python3 plugins/session-alarm/scripts/session_alarm.py setup
```

Requiere Python 3.9 o posterior. Usa `afplay` en macOS, `paplay`/`aplay`/`ffplay` en Linux y
`winsound` en Windows.

## Primera configuración

El asistente permite explorar y preescuchar el catálogo, añadir un WAV propio y asignar un sonido diferente a cada
uno de los cuatro eventos, elegir volumen y notificaciones de escritorio, y definir horas de
silencio que pueden cruzar la medianoche. Codex y Claude Code comparten la misma configuración.

```bash
# Mostrar el catálogo
python3 plugins/session-alarm/scripts/session_alarm.py catalog

# Escuchar el gato
python3 plugins/session-alarm/scripts/session_alarm.py preview cat --volume 70

# Escuchar los 12 sonidos en orden (detener: Ctrl+C)
python3 plugins/session-alarm/scripts/session_alarm.py preview-all --volume 40

# Añadir y preescuchar tu WAV (máximo 30 segundos / 32 MB)
python3 plugins/session-alarm/scripts/session_alarm.py custom add "./my-sound.wav" \
  --name "My Sound" --id my-sound --preview

# Probar los cuatro eventos
python3 plugins/session-alarm/scripts/session_alarm.py test all
```

## Catálogo de 12 grabaciones reales

| Familia | Animales |
|---|---|
| Mascotas | Gato, perro |
| Granja | Vaca, caballo, cerdo, cabra, oveja, gallo |
| Aves | Búho, cuervo |
| Criaturas pequeñas | Rana, grillo |

Los archivos están normalizados para notificaciones breves. Consulta la
[procedencia y licencia](../SOUND_LICENSE.md).

## Privacidad y licencia

La configuración, los WAV importados y la caché generada permanecen en `~/.config/session-alarm/` en macOS/Linux o
`%APPDATA%\session-alarm\` en Windows. No se guardan ni transmiten conversaciones o archivos y no
hay solicitudes de red. Consulta la [declaración de privacidad](../PRIVACY.md) y la
[política de seguridad](../SECURITY.md).

Los derechos del audio importado no cambian; usa solo audio propio o con una licencia válida.

El código y la documentación usan la [licencia MIT](../LICENSE). La procedencia CC0 de las
12 grabaciones integradas está documentada en
[procedencia y licencia](../SOUND_LICENSE.md).
Este es un proyecto independiente sin afiliación, respaldo ni patrocinio de OpenAI o Anthropic.
