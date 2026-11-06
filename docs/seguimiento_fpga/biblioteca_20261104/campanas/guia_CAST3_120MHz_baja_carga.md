# Prueba CAST3 a 120 MHz con baja carga

Usa las mismas fuentes y distribución 1/1/1 del resultado a 100 MHz. Hace una
síntesis e implementación nuevas con objetivo de 8,333333333 ns, incluida la
optimización física final Explore. Exporta timing de síntesis y timing final,
setup, hold, clocks, check_timing, DRC, metodología, bus skew y estado del ruteo.
El resultado a 100 MHz y el repositorio original se conservan.

Recursos del servicio, incluidos todos los procesos hijos:

- Un hilo de Vivado, un job a la vez y máximo agregado de un núcleo de CPU.
- Prioridad CPU baja (`nice 15`) y prioridad de disco idle. Se solicita también
  peso de I/O 10; este host no expone `io.weight` en el cgroup del servicio, por
  lo que la prioridad de disco verificada es la de los procesos (`ionice idle`).
- Regulación de memoria desde 4 GiB y máximo de 5 GiB de RAM más 5 GiB de swap.
  La implementación anterior llegó a unos 8 GB de pico de memoria; con este
  presupuesto puede tardar mucho más. Si no alcanza, el servicio falla y conserva
  los artefactos; no relanza automáticamente ni aumenta límites.
- Servicio independiente de esta terminal y bloqueo temporal de suspensión.

Esta prueba cambia el objetivo del análisis, no configura el clock físico del
PS, no genera bitstream ni programa la placa. La validación funcional existente
de CAST3 se reutiliza porque el RTL y la distribución de registros son iguales.

Lanzada el 4 de noviembre de 2026 a las 15:23 (Córdoba) como
`cva6-fpu120-low-da6bd612efe94a7d.service`. Los límites de CPU y memoria y las
prioridades de procesos se verificaron en el kernel; el registro está en
`prueba_120MHz_20261104_baja_carga/resource_limits_observed.json`.

## Preparar y lanzar una copia nueva

```bash
cd /home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz
python3 run_120_low_resource.py prepare \
  --baseline "$PWD/recuperacion_20261104" \
  --output "$PWD/prueba_120MHz_20261104_baja_carga"
bash prueba_120MHz_20261104_baja_carga/code/lanzar_120_baja_carga.sh \
  "$PWD/prueba_120MHz_20261104_baja_carga"
```

La preparación rechaza una salida existente. El lanzador rechaza un servicio o
lanzamiento previo: estos comandos no reinician una prueba ya iniciada.

## Consultar y controlar la ejecución

`service.json` guarda el nombre exacto del servicio. Para consultarlo:

```bash
cd /home/nachofalchi/Documents/ChatGPT/Tesis/Automatizacion-FPU-100MHz/prueba_120MHz_20261104_baja_carga
unit=$(python3 -c 'import json; print(json.load(open("service.json"))["unit"])')
systemctl --user show "$unit" \
  -p ActiveState -p SubState -p Result -p ExecMainStatus \
  -p CPUUsageNSec -p MemoryCurrent -p MemoryPeak -p MemorySwapCurrent
tail -n 20 driver.log
cat cast3/reports/execution.json
```

El servicio es la fuente de verdad ante una interrupción o falta de memoria:
un proceso terminado por OOM puede dejar `state.json` en `running`. Una salida
3 significa corrida completa con timing incumplido; una salida 2 significa error
o evidencia inválida. Ninguna de las dos se presenta como cierre.

Para liberar recursos mientras usás la computadora, podés suspender y retomar
todos los procesos de la prueba conservando el estado en memoria:

```bash
systemctl --user freeze "$unit"
systemctl --user thaw "$unit"
```

Para detenerla definitivamente: `systemctl --user stop "$unit"`. Detenerla no
borra resultados, pero no hay recuperación automática de una corrida parcial.

Al terminar, `cast3/reports/result.json` y `comparison.json` registran el veredicto
y la comparación con 100 MHz. El clasificador requiere reporte final completo,
sin violaciones activas de restricciones ni errores de ruteo. Conserva la misma
lista auditada de 75 pines inactivos de clock constante del diseño de 100 MHz.
