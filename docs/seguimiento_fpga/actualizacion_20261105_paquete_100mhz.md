# Paquete de CAST3 a 100 MHz y resultado final de 120 MHz

Corte: **5 de noviembre de 2026, 23:50, hora de Córdoba**. Plataforma KR260,
K26 `xck26-sfvc784-2LV-c`, Vivado 2026.1, top `kr260_top`. Continúa el
[registro del 4 de noviembre](actualizacion_20261104_cast.md), que conserva su
corte de las 16:53:58.

**Ya existe un paquete para probar CAST3 en placa a 99,999 MHz, pero todavía no se
ejecutó en hardware.** Sale del checkpoint que cerró a 10 ns e incluye bitstream,
XSA y FSBL. Las dos corridas nuevas no cerraron timing: la implementación con el PS
configurado a 100 MHz y la prueba a 120 MHz. CAST3 del 4 de noviembre a las 14:50
sigue siendo la referencia.

## Resultados

Todos los márgenes están en ns.

| Corrida de CAST3 (1/1/1) | Período | WNS | TNS | Setup negativos | WHS | Veredicto |
|---|---:|---:|---:|---:|---:|---|
| Cierre de las 14:50, PS en IOPLL/11 | 10 | **0,000** | **0,000** | **0 de 96.648** | 0,000 | Cerró; origen del paquete |
| Implementación nueva, PS en IOPLL/10, 20:52 | 10 | −0,208 | −90,293 | 1.014 de 96.693 | 0,000 | Sin cierre ni bitstream |
| Prueba a 120 MHz, 19:19 | 8,333 | −1,806 | −10.882,976 | 18.654 de 96.670 | +0,003 | Sin cierre ni bitstream |

Las dos corridas nuevas terminaron sin errores de Vivado, con hold cumplido y sin
errores de ruteo, por lo que son resultados válidos de timing. Sus servicios figuran
como `failed` porque el controlador sale con código 3 cuando no hay cierre.

La implementación con IOPLL/10 hizo también `AggressiveExplore`. Su WNS pasó de
−0,580 a −0,283 ns con `Explore` y a −0,208 ns con esa pasada. La
[comparación de implementaciones](comparacion_implementaciones_100mhz_20261104.md)
explica por qué dio distinto de la corrida que cerró.

A 120 MHz solo hizo la pasada final `Explore`. Entre sus 100 peores caminos, las
fuentes principales son `csr_regfile_i` (43), `ex_stage_i` (26) e `issue_stage_i`
(17). Esos 100 caminos son una muestra de los 18.654 endpoints que fallan.

## Paquete generado

Está en
`/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/paquete_100mhz_desde_cast3/`,
fuera del repositorio. Su [`LEEME.md`](/home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/paquete_100mhz_desde_cast3/LEEME.md)
resume el contenido, y `SHA256SUMS.txt` guarda los hashes completos.

| Archivo | Contenido | SHA256 (inicio) |
|---|---|---|
| `kr260_top.bit` | Bitstream del checkpoint cerrado | `e74c691b451616b7` |
| `kr260_top.ltx` | Sondas de depuración | `f12e1966ba028d72` |
| `kr260_cva6_100mhz.xsa` | Ese bitstream y los archivos del PS con IOPLL/10 | `9585a450f4e89032` |
| `kr260_fsbl_100mhz_patched.elf` | FSBL con IOPLL/10 y parche de reset | `721713089fe100b5` |
| `kr260_top_100mhz_closed.dcp` | Copia del checkpoint cerrado | `4c7dadcac240b21a` |

### Por qué el checkpoint cerrado sirve a 100 MHz

El reloj de PL0 lo programa el FSBL, no el bitstream. El checkpoint se analizó a
10 ns, aunque guarda el PS configurado con IOPLL/11. Sus archivos del PS difieren de
los de IOPLL/10 en metadatos de frecuencia y jitter, y el checksum de síntesis es el
mismo (`2d5da2aa`). Su incertidumbre de reloj fue 0,166 ns, 6 ps más que los 0,160 ns
calculados con IOPLL/10.

### Cómo se armó y qué se comprobó

- **Bitstream:** al reabrir el checkpoint, WNS/TNS y WHS/THS repitieron
  0,000/0,000 ns a 10 ns. Las 88.125 redes quedaron ruteadas y el DRC del bitstream
  terminó con 0 errores.
- **XSA:** parte del XSA generado desde el checkpoint cerrado y reemplaza `psu_init.c`,
  `psu_init_gpl.c`, `psu_init.tcl`, `psu_init.html` y `kr260_ps_ddr_bd.hwh` por los de
  la corrida con IOPLL/10. Esos archivos solo difieren en la frecuencia de PL0 y la
  fecha del `hwh`. El registro de PL0 queda en `0x01010A00`.
- **FSBL:** HSI abrió el XSA, generó las fuentes con el mismo `psu_init.c` y compilaron
  sin errores. Frente al FSBL de 90,9 MHz cambian 3 líneas de `psu_init.c`, dos
  instrucciones y la fecha y hora de compilación. Las demás secciones cargadas son
  idénticas. Es una comprobación de compilación: el FSBL no se ejecutó.
- **Sondas:** los 632 nombres del `.ltx` coinciden con los del paquete de 90,9 MHz.

**No regenerar el XSA desde el checkpoint cerrado.** `write_hw_platform` volvería a
escribir IOPLL/11 y el FSBL dejaría el reloj en 90,9 MHz. Los scripts son
`exportar_100_desde_cast3.sh`, `combinar_xsa_100.py` y `compilar_fsbl_100.py`, en la
carpeta de la campaña.

## Cómo probarlo en placa

`cva6 ensayo` acepta 100 MHz desde el 5 de noviembre. Primero repetir la referencia
conocida y después la prueba nueva:

```bash
cva6 ensayo --frecuencia 25 --ejecutar
cva6 ensayo --frecuencia 100 --con-ila --ejecutar
```

Sin `--ejecutar` solo genera el plan, que comprueba los hashes del paquete y la prueba
de compilación del FSBL. Al ejecutar, lee el registro de PL0 y se detiene si no coincide
con `0x01010A00`. Los planes reales de 25, 91 y 100 MHz salieron sin bloqueos, y las
pruebas automáticas simulan la placa. **El flujo no se ejecutó con hardware.**

Esta prueba escribe patrones en la DDR y comprueba que la BootROM termine en PASS. No
ejercita la FPU, y un PASS no mide la frecuencia alcanzada ni reemplaza el STA.
`cva6 verificar` y `cva6 preparar-manana` siguen cubriendo solo 25 y 90,9 MHz. Ver la
[guía de automatización](../../../automatizacion/README.md).

## Otros cambios en `fpnew_cast_multi.sv`

El registro anterior describe el cambio de reparto de registros. El archivo usado, igual
al que aportó un compañero (SHA256 `a617728ffbc2f957`, sin commit en el repositorio),
incluye además:

- **Extensión de signo:** corrige el resultado de `fcvt.w` y `fcvt.wu` en RV64, igual que
  el commit oficial `17f1561cd`. Por lo tanto, cambia resultados y no solo timing.
- **Salida `early_out_valid_o`:** agregada por el commit oficial `fc2f8a2e3`. No se usa en
  este diseño.

En la revisión del 4 de noviembre, el banco de CAST pasó con las semillas 1 a 6. La
comparación de la versión anterior con la actual, sobre 1.500.005 vectores, dio 9.508
diferencias, todas en el resultado o el bit de extensión de conversiones de flotante a
entero, y ninguna en flags. Cuatro casos límite con flags incorrectos ya existían antes
del cambio. Los archivos de esa simulación no forman parte de este registro.

## Pendientes

1. Repetir la referencia de 25 MHz y correr la prueba de 100 MHz con ILA. Registrar
   PASS/FAIL y la captura.
2. Correr pruebas de punto flotante con el procesador completo. Hasta ahora solo se
   simuló el bloque CAST.
3. Pasar CAST3 al repositorio si se adopta. El repositorio conserva `LAT_CONV=2`, y
   `fpnew_cast_multi.sv` no tiene commit.
4. Actualizar `fp_cvt.opLat = 2` a 3 en
   `gem5_config_CVA6/gem5/gem5_config_CVA6.py:80` para modelar CAST3.
5. Respaldar el paquete y el checkpoint cerrado: están solo en esta computadora y fuera
   del alcance de `cva6 respaldo`.

## Evidencia

- [Métricas y hashes de este corte](auditorias/timings_20261105.json).
- [Manifiesto de la actualización](auditorias/actualizacion_20261105_manifest.json),
  [hashes](SHA256SUMS_20261105.txt) y
  [archivo documental](archivo_documental_20261105_100mhz.tar.gz).
- Reportes en `Automatizacion-FPU-100MHz/`: `implementacion_100MHz_reloj_real/cast3/reports/`,
  `prueba_120MHz_20261104_baja_carga/cast3/reports/` y
  `paquete_100mhz_desde_cast3/reportes/`.
- Comprobaciones del FSBL en
  `paquete_100mhz_desde_cast3/fsbl_100mhz/fsbl100_manifest.json`.
