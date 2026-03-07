# ATC_MiThermometer — Claude Notes

## Project Overview

Firmware for Xiaomi BLE thermometers (MJWSD06MMC and others). Written in C for the TLSR8258 chip.
Built with GCC for embedded target. IDE uses clangd for diagnostics.

## Key Architecture

- `src/app.c` — main loop, button handling, flash init, global state
- `src/app.h` — all major typedefs, externs, and constants
- `src/app_config.h` — compile-time feature flags (device type, services, USE_THERMOSTAT, etc.)
- `src/cmd_parser.c` — BLE command dispatch (get/set over RxTx characteristic)
- `src/cmd_parser.h` — CMD_ID_* enum for all BLE commands
- `src/ble.c` / `src/ble.h` — BLE send helpers (ble_send_cmf, ble_send_thermostat, etc.)
- `src/lcd.c` — device-agnostic LCD logic (comfort check, lcd() render function)
- `src/lcd_mjwsd06mmc.c` — MJWSD06MMC screen driver: segment symbols, show_big_number_x10, show_off, etc.
- `src/flash_eep.c` — flash key-value store (flash_read_cfg / flash_write_cfg)

## Flash Storage Pattern

Config structs are stored with `flash_write_cfg(&struct, EEP_ID_*, sizeof(struct))`.
On read, `flash_read_cfg` returns the stored size. Callers check `returned_size == sizeof(struct)` and fall back to defaults if mismatch.

**Adding a field to a flash-stored struct:** appending is safe — old firmware data causes a size mismatch on first boot, triggering a reset to defaults. Acceptable for non-critical config. Always add a `.field = default` entry in the corresponding `def_*` initializer.

## scomfort_t / cmf

Stored under `EEP_ID_CMF`. Contains:
- `s16 t[2]` — comfort temp range (x0.01 °C)
- `u16 h[2]` — comfort humidity range (x0.01 %)
- `u8 thermostat_enabled` — (ifdef USE_THERMOSTAT) thermostat on/off flag, default 0

`CMD_ID_COMFORT` (0x20) sets only t[]/h[] — deliberately capped to `sizeof(t)+sizeof(h)` when USE_THERMOSTAT is defined to protect `thermostat_enabled`.
`CMD_ID_THERMOSTAT` (0x2d) gets/sets `thermostat_enabled` separately.

## Thermostat Feature (USE_THERMOSTAT)

Single-button UI using `setpoint_mode_t` in `app.h`:
- `mode_active = 0` — normal display
- `mode_active = 1` — adjusting setpoint (blinks temperature)
- `mode_active = 2` — oFF state (blinks "oFF")

**Button press logic (app.c):**
- Not in mode + thermostat on → mode 1, new_setpoint = cmf.t[0]
- Not in mode + thermostat off → mode 2, new_setpoint = cmf.t[0] (preloaded for next press)
- In mode 1 → increment by SETPOINT_STEP; if > SETPOINT_MAX_TEMP → new_setpoint = SETPOINT_MIN_TEMP, mode 2
- In mode 2 → mode 1 (new_setpoint already primed: MIN if came from cycling, saved setpoint if came from thermostat-off)

**Timeout commit logic (app.c):**
- Timeout in mode 2 → `thermostat_enabled = 0`, save cmf to flash, exit
- Timeout in mode 1 → `thermostat_enabled = 1`, save new_setpoint to cmf.t[0], save cmf to flash, exit

**LCD rendering (lcd.c):**
- mode 1 → blink temperature via `show_big_number_x10` + `show_temp_symbol`
- mode 2 → blink "oFF" via `show_off()`

## LCD Segment Display (MJWSD06MMC)

`display_buff[3..5]` = big number area (left to right: [5][4][3]).
`display_numbers[]` has 0-F; index 15 = "F".
Predefined symbols: `LCD_SYM1_o`, `LCD_SYM1_L`, `LCD_SYM1_H`, etc.
`show_off()` writes: `display_buff[5]=LCD_SYM1_o`, `[4]=display_numbers[15]`, `[3]=display_numbers[15]`.

## Preprocessor / Build Notes

- `lcd.c` is only compiled for non-MJWSD05MMC devices (`#if !MJWSD05MMC`). All includes and function bodies are inside that guard.
- All thermostat-specific code is wrapped in `#ifdef USE_THERMOSTAT` / `#endif` throughout.

## BLE Command Pattern

To add a new get/set command:
1. Add `CMD_ID_FOO = 0xNN` to enum in `cmd_parser.h` (wrap in `#ifdef` if feature-gated)
2. Add `ble_send_foo()` in `ble.c` + declare in `ble.h` (same guard)
3. Add handler in the `cmd_parser.c` dispatch chain (inside appropriate `#if SERVICE_*` block)
