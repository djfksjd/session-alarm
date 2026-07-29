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
  <img alt="40 sonidos" src="https://img.shields.io/badge/sonidos_de_animales-40-FFB703?style=flat-square">
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

Los 40 sonidos se generan con recetas originales de modelado acústico a 44,1 kHz. No incluyen
grabaciones, efectos de stock, clips generados por IA, voces famosas ni muestras de terceros.
También puedes añadir un WAV creado por ti o con licencia; el archivo permanece en tu equipo.

<table>
  <tr>
    <td width="25%" align="center"><strong>🔔 Determinista</strong><br>Los hooks del ciclo de vida funcionan sin depender de la memoria del modelo.</td>
    <td width="25%" align="center"><strong>🐊 40 animales</strong><br>Desde gatos y patos hasta cocodrilos, elefantes, hienas y ballenas.</td>
    <td width="25%" align="center"><strong>🛡️ Audio original</strong><br>Sin memes, famosos, emisiones, efectos de stock ni muestras externas.</td>
    <td width="25%" align="center"><strong>🏠 Solo local</strong><br>Sin cuenta, servidor, análisis, telemetría ni solicitudes de red.</td>
  </tr>
</table>

## Cuándo suena

| Evento | Codex | Claude Code | Predeterminado |
|---|---|---|---|
| Necesita respuesta | Solicitud de permiso o respuesta que termina en pregunta | Permiso, diálogo, agente en segundo plano o pregunta | Pato |
| Trabajo terminado | Fin de la respuesta actual | Fin de respuesta o agente en segundo plano terminado | Gallo |
| Error | Evento de error disponible | `StopFailure` | Rana |
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

# Escuchar el cocodrilo
python3 plugins/session-alarm/scripts/session_alarm.py preview crocodile --volume 70

# Escuchar los 40 sonidos en orden (detener: Ctrl+C)
python3 plugins/session-alarm/scripts/session_alarm.py preview-all --volume 40

# Añadir y preescuchar tu WAV (máximo 30 segundos / 32 MB)
python3 plugins/session-alarm/scripts/session_alarm.py custom add "./my-sound.wav" \
  --name "My Sound" --id my-sound --preview

# Probar los cuatro eventos
python3 plugins/session-alarm/scripts/session_alarm.py test all
```

## Catálogo de 40 sonidos

| Familia | Animales |
|---|---|
| Mascotas | Gato, gatito, perro, cachorro |
| Granja | Vaca, caballo, burro, cerdo, cabra, oveja, pato, ganso, gallina, gallo, pavo |
| Salvajes | Lobo, zorro, león, elefante, mono, oso, cocodrilo, hiena, camello, mapache, hipopótamo, serpiente |
| Aves | Búho, cuervo, gorrión, águila, pavo real, pingüino |
| Criaturas pequeñas | Rana, grillo, abeja, mosquito |
| Océano | Delfín, foca, ballena |

Cada nombre describe un diseño sonoro original inspirado en ese animal, no una grabación de campo.
Consulta la [procedencia y licencia](../SOUND_LICENSE.md).

## Privacidad y licencia

La configuración, los WAV importados y la caché generada permanecen en `~/.config/session-alarm/` en macOS/Linux o
`%APPDATA%\session-alarm\` en Windows. No se guardan ni transmiten conversaciones o archivos y no
hay solicitudes de red. Consulta la [declaración de privacidad](../PRIVACY.md) y la
[política de seguridad](../SECURITY.md).

Los derechos del audio importado no cambian; usa solo audio propio o con una licencia válida.

El código usa la [licencia MIT](../LICENSE) y los WAV generados solo a partir de las recetas
originales se ofrecen bajo [CC0 1.0](../SOUND_LICENSE.md).
Este es un proyecto independiente sin afiliación, respaldo ni patrocinio de OpenAI o Anthropic.
