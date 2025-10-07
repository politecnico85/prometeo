# prometeo
Source Code for Software Testing

Introducción a Domain-Driven Design (DDD) Aplicado a Este Modelo
Domain-Driven Design (DDD) es un enfoque para desarrollar software que se centra en modelar el dominio del negocio de manera que el código refleje el lenguaje y los conceptos del negocio real. En este caso, el dominio es un sistema de facturación e inventario, con conceptos como productos, sucursales, bodegas, facturas, descuentos, movimientos de inventario (usando FIFO) y notas de crédito.
Principios clave de DDD que aplicaremos:

Entities: Objetos con identidad única (e.g., un Producto específico con ID).
Value Objects: Objetos inmutables sin identidad propia (e.g., una Dirección o un Precio).
Aggregates: Grupos de entities y value objects tratados como una unidad atómica (e.g., Factura con sus líneas y totales).
Repositories: Interfaces para acceder y persistir aggregates en la base de datos.
Domain Services: Lógica de negocio que no pertenece a una sola entity (e.g., calcular descuentos o manejar FIFO).
Ubiquitous Language: Usar términos del dominio como "Factura", "MovimientoInventario", etc., directamente en el código.

Usaremos Python con bibliotecas como dataclasses para models simples, y asumiré un ORM como SQLAlchemy para persistencia (puedes integrarlo). El código será modular, con paquetes como domain para el núcleo del negocio, separado de infraestructura (e.g., DB).
Enfocaré en aggregates clave: Producto (con inventario y precios), Factura (con líneas y totales), y MovimientoInventario (con FIFO). No implementaré todo el esquema para brevedad, pero puedes extenderlo.
Estructura de Paquetes Sugerida
textmi_proyecto/
├── domain/
│   ├── entities/
│   │   ├── producto.py
│   │   ├── factura.py
│   │   ├── movimiento_inventario.py
│   │   └── ... (otras entities)
│   ├── value_objects/
│   │   ├── direccion.py
│   │   ├── precio.py
│   │   └── ... 
│   ├── aggregates/
│   │   ├── producto_aggregate.py
│   │   ├── factura_aggregate.py
│   │   └── ...
│   ├── repositories/
│   │   ├── producto_repository.py
│   │   └── ...
│   └── services/
│       ├── inventario_service.py
│       └── factura_service.py
├── infrastructure/
│   └── persistence/
│       └── sql_repository.py  # Implementación con SQLAlchemy
└── application/
    └── main.py  # Ejemplo de uso



Notas Finales

Integración con DB: Usa SQLAlchemy o otro ORM para mapear el esquema SQL completo. Implementa triggers y procedures (como after_movimiento_insert y RegistrarSalidaFIFO) como domain events o en services.
Eventos de Dominio: Para cosas como "stock bajo", usa un event bus (e.g., con pydispatch).
Validaciones: Agrega invariants en aggregates (e.g., total no negativo).
Escalabilidad: Separa bounded contexts si crece (e.g., Inventario vs. Facturación).
Testing: Usa unit tests para services y aggregates, mocks para repositories.

Esto es una base; adáptalo a tus necesidades. Si necesitas código para partes específicas (e.g., NotaCredito), ¡házmelo saber!


2.

Aggregates en DDD para Factura: Profundización
En Domain-Driven Design (DDD), un aggregate es un clúster de entidades y value objects que se tratan como una unidad atómica para mantener la consistencia del dominio. La Factura es un aggregate natural en este sistema de facturación, ya que representa un documento comercial completo que debe ser consistente internamente (e.g., las líneas deben sumar correctamente a los totales, los descuentos deben aplicarse de forma válida, y las operaciones como emisión deben impactar el inventario de manera transaccional).
El aggregate de Factura tiene como raíz (aggregate root) a la entidad Factura, que orquesta el acceso y las mutaciones. Incluye:

Entidades hijas: Líneas de factura (LineaFactura), totales (TotalesFactura).
Value Objects: Elementos inmutables como Direccion, Precio, FormaPago.
Referencias externas: IDs a otros aggregates como Producto, Sucursal, Bodega, Descuento (no se cargan completos para evitar acoplamiento; se usan repositories para lazy loading si es necesario).
Invariantes: Reglas de negocio que deben cumplirse siempre, e.g., el total no puede ser negativo, la suma de líneas debe coincidir con los totales, stock suficiente antes de emisión.
Domain Events: Para decoupled communication, e.g., FacturaEmitida podría disparar un evento para registrar movimientos de inventario (salida FIFO).

No incluimos NotaCredito en este aggregate, ya que es un aggregate separado (referencia a Factura por ID, pero con su propio ciclo de vida). Esto mantiene bounded contexts: Facturación vs. Ajustes Post-Venta.
Estructura Detallada del Aggregate
Usaremos Python con dataclasses para simplicidad, y asumiremos un ORM como SQLAlchemy para persistencia (en infrastructure layer). Agregaré métodos para operaciones de dominio, validaciones y eventos.
Primero, value objects relevantes (extensión de lo anterior):




Consideraciones Avanzadas

Consistencia Eventual: Para grandes sistemas, usa CQRS/ES: Almacena eventos como LineaAgregada, DescuentoAplicado, y reconstruye el aggregate.
Validaciones de Dominio: Usa specifications pattern para reglas complejas (e.g., "FacturaValidaParaEmisionSpec").
Manejo de Concurrencia: Optimistic locking con versión en la root.
Testing: Unit test el aggregate aislado (mocks para services), integration test con DB real.
Mapeo a DB: En infrastructure, usa ORM para mapear tablas (Factura -> LineaFactura con cascade, TotalesFactura como embedded o separate).

Esto profundiza el aggregate, enfocándose en consistencia y negocio. Si necesitas código para NotaCredito como aggregate relacionado, o implementación SQLAlchemy, avísame.



Aggregates en DDD para NotaCredito: Profundización
Similar al aggregate de Factura, el NotaCredito es un aggregate independiente en el dominio de facturación, representando un documento de ajuste post-venta (e.g., devoluciones, correcciones). Mantiene consistencia interna: las líneas deben sumar a los totales, el motivo de modificación debe ser válido, y debe referenciar una Factura existente sin cargar su aggregate completo (para evitar acoplamiento; usa ID y repositories para consultas).

Aggregate Root: NotaCredito (entidad principal).
Entidades Hijas: LineaNotaCredito, TotalesNotaCredito.
Value Objects: Reusa existentes como Direccion, RUC, y agrega si es necesario (e.g., MotivoModificacion como value object para encapsular texto con validaciones).
Referencias Externas: ID a Factura (id_factura_modificada), Sucursal.
Invariantes: Totales consistentes, referencia a factura válida, cantidades no superiores a las de la factura original.
Relación con Factura: NotaCredito impacta inventario (e.g., entradas por devoluciones) vía services, disparando eventos como NotaCreditoEmitida para actualizar stock (posiblemente reversando FIFO).
Domain Events: NotaCreditoEmitida podría triggering ajustes en inventario o contabilidad.

No incluimos Factura en este aggregate; es una referencia externa. Usa un service para orquestar creación (validando contra la factura original).
Usamos Python con dataclasses. Asumimos reuso de value objects de Factura (e.g., RUC, Direccion).
Value Objects Adicionales




Integración con Repositories y Services
Similar a Factura:

Repository: NotaCreditoRepository para cargar/guardar el aggregate.
Service: NotaCreditoService para creación/emisión, validando contra FacturaRepository (e.g., chequear cantidades <= líneas de factura).

Ejemplo de service:




Notas

Relación con Inventario: Para devoluciones, implementa registrar_entrada en InventarioService (agregando a lotes nuevos o reversando FIFO).
Validaciones Adicionales: En service, compara líneas con las de la factura original.
Persistencia: Mapear con ORM (e.g., SQLAlchemy) similar a Factura.
Extensión: Si necesitas eventos o más integraciones, avísame.

Este aggregate está relacionado con Factura vía referencia, manteniendo separación de concerns.




Optimización de Validaciones en el Aggregate de NotaCredito
Para optimizar las validaciones en el aggregate NotaCreditoAggregate, aplicaremos principios de DDD como invariantes explícitos, separación de responsabilidades, y el patrón Specification (si aplica) para encapsular reglas de negocio complejas. El objetivo es:

Claridad: Hacer las validaciones legibles y mantenibles.
Reusabilidad: Centralizar reglas para usar en múltiples aggregates/services.
Eficiencia: Minimizar redundancias y consultas innecesarias.
Robustez: Asegurar consistencia sin afectar rendimiento.

Nos enfocaremos en el aggregate NotaCreditoAggregate, optimizando las validaciones en emitir, _verificar_invariantes, y creación, considerando la relación con Factura. También mejoraremos la validación contra la factura original (e.g., cantidades no excedan las originales) y las reglas de negocio (e.g., totales consistentes, motivo válido).
Usaremos el patrón Specification para reglas complejas, moviendo validaciones externas (como chequeo de factura) al NotaCreditoService. Esto mantiene el aggregate ligero y enfocado en su consistencia interna. También reduciremos duplicación de código y mejoraremos la extensibilidad.
Código Optimizado
Primero, definimos specifications para encapsular reglas de negocio.




#### Service con Validaciones Externas
Movemos la validación contra la factura al service, manteniendo el aggregate enfocado.



#### Cambios y Optimizaciones
1. **Specifications Pattern**:
   - Encapsula reglas en clases reutilizables (`NotaCreditoTieneLineas`, etc.).
   - Permite combinar reglas con `CompositeSpecification` (usando `&` para AND lógico).
   - Mantiene el aggregate limpio, moviendo validaciones complejas (e.g., contra factura) al service.
2. **Validaciones Externas**:
   - La validación contra `Factura` se delega al service, usando `LineasValidasContraFactura`. Esto reduce el acoplamiento en el aggregate.
   - El aggregate solo valida invariantes internos (líneas, totales, motivo).
3. **Centralización de Errores**:
   - `_verificar_invariantes` acumula errores en una lista, arrojando un mensaje consolidado.
   - Mejora la depuración al especificar qué regla falló.
4. **Eficiencia**:
   - Evita recalcular totales innecesariamente (se manejan en `NotaCredito._actualizar_totales`).
   - Lazy loading de factura vía repository en el service.
5. **Extensibilidad**:
   - Agregar nuevas validaciones es tan simple como crear una nueva `Specification` y añadirla a `_validaciones`.
   - Soporta reglas complejas (e.g., validar IVA según tipo de producto) sin modificar el aggregate.
6. **Manejo de Eventos**:
   - `emitir` está listo para disparar eventos (NotaCreditoEmitida), que pueden ser manejados por un event bus (no implementado aquí).
7. **Robustez**:
   - Validaciones explícitas en value objects (`MotivoModificacion`, `LineaNotaCredito`) evitan estados inválidos desde la creación.

#### Notas
- **Persistencia**: Usa SQLAlchemy para mapear `NotaCredito`, `LineaNotaCredito`, y `TotalesNotaCredito` (similar a Factura). Asegura transacciones atómicas en `NotaCreditoRepository`.
- **Concurrencia**: Agrega optimistic locking (e.g., campo `version` en `NotaCredito`) para evitar conflictos.
- **Testing**: Escribe unit tests para specifications y aggregate, usando mocks para `InventarioService` y `FacturaAggregate`.
- **Extensión**: Si necesitas integrar más validaciones (e.g., fechas, límites de crédito), añade specifications adicionales.


Implementación de Validaciones de Fechas en el Aggregate de NotaCredito
Para optimizar las validaciones de fechas en el aggregate NotaCreditoAggregate, integraremos reglas específicas relacionadas con las fechas (fecha_emision, fecha_caducidad, y fecha_autorizacion) en el contexto del dominio de facturación. Estas validaciones se alinearán con los principios de DDD, utilizando el patrón Specification para encapsular las reglas de negocio y mantener el aggregate enfocado en su consistencia interna. Las validaciones se centrarán en:

Reglas de Negocio para Fechas:

fecha_emision debe ser igual o posterior a la fecha actual.
fecha_caducidad debe ser posterior a fecha_emision (si existe).
fecha_autorizacion debe ser igual o anterior a fecha_emision y no futura.
La fecha_emision de la nota de crédito debe ser posterior a la fecha_emision de la factura modificada.
Opcional: Validar que la nota de crédito se emita dentro de un plazo razonable desde la factura (e.g., 30 días, configurable).


Optimizaciones:

Usar specifications para reglas reutilizables y combinables.
Mover validaciones externas (como comparación con la factura) al NotaCreditoService.
Centralizar manejo de errores para claridad.
Aprovechar Python datetime para cálculos precisos de fechas.


Integración:

Las validaciones se aplicarán en el aggregate durante operaciones clave (crear_nueva, agregar_linea, emitir).
La validación contra la factura modificada se delegará al service, usando FacturaRepository.



Asumimos que las entidades y value objects (NotaCredito, LineaNotaCredito, TotalesNotaCredito, RUC, Direccion, MotivoModificacion) ya están definidos como en los ejemplos previos. Extenderemos el código de nota_credito_aggregate.py y nota_credito_service.py para incluir validaciones de fechas, y actualizaremos nota_credito_specifications.py con nuevas specifications.
Specifications para Validaciones de Fechas
Extendemos el módulo de specifications para incluir reglas de fechas.






#### Cambios y Optimizaciones
1. **Nuevas Specifications de Fechas**:
   - `FechaEmisionValida`: Asegura que `fecha_emision` no sea anterior a hoy.
   - `FechaCaducidadValida`: Verifica que `fecha_caducidad` sea posterior a `fecha_emision` (si existe).
   - `FechaAutorizacionValida`: Garantiza que `fecha_autorizacion` no sea futura y esté antes o igual a `fecha_emision`.
   - `FechaEmisionPosteriorFactura` y `PlazoNotaCreditoValido`: Validan contra la factura, ejecutadas en el service.
2. **Integración en Aggregate**:
   - Las specifications internas (`FechaEmisionValida`, etc.) se añaden a `_validaciones` en el aggregate.
   - Se valida al crear (`crear_nueva`) y en operaciones críticas (`agregar_linea`, `emitir`).
3. **Service para Validaciones Externas**:
   - Validaciones que requieren `FacturaAggregate` (`FechaEmisionPosteriorFactura`, `PlazoNotaCreditoValido`) se ejecutan en el service.
   - Esto mantiene el aggregate ligero y desacoplado.
4. **Manejo de Errores**:
   - Errores de validación se acumulan en listas, proporcionando mensajes claros.
   - `ValueError` consolida todas las fallas para facilitar depuración.
5. **Flexibilidad**:
   - `PlazoNotaCreditoValido` permite configurar el máximo de días (default: 30).
   - Fechas opcionales (`fecha_caducidad`) tienen manejo seguro.
6. **Robustez**:
   - Default values en `NotaCredito` (`fecha_emision`, `fecha_autorizacion` como hoy, `fecha_caducidad` como +30 días) reducen errores.
   - Specifications son reutilizables para otros aggregates (e.g., Factura).

#### Notas
- **Persistencia**: Asegura que `NotaCreditoRepository` mapee fechas correctamente con SQLAlchemy (usa `Date` para columnas).
- **Testing**: Escribe unit tests para specifications (e.g., probar `FechaEmisionValida` con fechas pasadas/futuras) y integration tests para el service.
- **Extensión**: Si necesitas validaciones adicionales (e.g., restricciones legales por país), añade specifications o parámetros configurables.
- **Eventos**: Podrías disparar un evento `NotaCreditoCreada` en el service para auditoría.

Se necesita integrar estas validaciones en `FacturaAggregate` o implementar `InventarioService.registrar_entrada`





Implementación de Validaciones de Fechas en el Aggregate de Factura
Para optimizar las validaciones de fechas en el aggregate FacturaAggregate, integraremos reglas específicas relacionadas con las fechas (fecha_emision, fecha_caducidad, y fecha_autorizacion) en el contexto del dominio de facturación, siguiendo los principios de Domain-Driven Design (DDD). Usaremos el patrón Specification para encapsular las reglas de negocio, manteniendo el aggregate enfocado en su consistencia interna y delegando validaciones externas (si las hay) al FacturaService. Las validaciones se centrarán en:

Reglas de Negocio para Fechas:

fecha_emision debe ser igual o posterior a la fecha actual.
fecha_caducidad debe ser posterior a fecha_emision (si existe).
fecha_autorizacion debe ser igual o anterior a fecha_emision y no futura.
Opcional: Validar que la factura no se emita en un estado inválido (e.g., sin stock suficiente, aunque esto se delega a InventarioService).


Optimizaciones:

Usar specifications para reglas reutilizables y combinables.
Centralizar manejo de errores para claridad y depuración.
Minimizar redundancias en validaciones.
Aprovechar Python datetime para cálculos precisos de fechas.


Integración:

Las validaciones se aplicarán en el aggregate durante operaciones clave (crear_nueva, agregar_linea, emitir).
La validación de stock (relacionada con MovimientosInventario) se delegará a InventarioService, manteniendo el aggregate ligero.



Asumimos que las entidades y value objects (Factura, LineaFactura, TotalesFactura, RUC, Direccion, FormaPago) están definidos como en los ejemplos previos. Reusaremos el módulo specifications para compartir lógica con NotaCreditoAggregate y extenderemos el código de factura_aggregate.py y factura_service.py para incluir validaciones de fechas.
Specifications para Validaciones de Fechas
Extendemos el módulo de specifications, compartiendo lógica común con NotaCredito.





#### Cambios y Optimizaciones
1. **Specifications de Fechas**:
   - `FechaEmisionValida`: Garantiza que `fecha_emision` no sea anterior a hoy.
   - `FechaCaducidadValida`: Verifica que `fecha_caducidad` sea posterior a `fecha_emision` (si existe).
   - `FechaAutorizacionValida`: Asegura que `fecha_autorizacion` no sea futura y esté antes o igual a `fecha_emision`.
2. **Integración en Aggregate**:
   - Las specifications (`FechaEmisionValida`, etc.) se añaden a `_validaciones` en el aggregate.
   - Se valida al crear (`crear_nueva`), agregar líneas (`agregar_linea`), y emitir (`emitir`).
3. **Service Simplicidad**:
   - No se requieren validaciones externas de fechas, ya que `Factura` no depende de otros aggregates para fechas (a diferencia de `NotaCredito`).
   - El service pasa fechas opcionales al aggregate, con valores por defecto seguros.
4. **Manejo de Errores**:
   - `_verificar_invariantes` acumula errores en una lista, proporcionando mensajes claros (e.g., "Validación fallida: FechaEmisionValida").
5. **Flexibilidad**:
   - Fechas opcionales (`fecha_caducidad`) se manejan con `None`, permitiendo configuraciones flexibles.
   - Specifications son reutilizables (compartidas con `NotaCredito`).
6. **Robustez**:
   - Default values en `Factura` (`fecha_emision` y `fecha_autorizacion` como hoy, `fecha_caducidad` como +30 días) previenen estados inválidos.
   - Validaciones en el aggregate aseguran consistencia interna.

#### Notas
- **Persistencia**: Usa SQLAlchemy para mapear `Factura`, `LineaFactura`, y `TotalesFactura`, asegurando que las columnas de tipo `Date` (`fecha_emision`, etc.) se manejen correctamente.
- **Testing**: Escribe unit tests para specifications (e.g., probar `FechaEmisionValida` con fechas pasadas) y integration tests para `FacturaService` con DB real.
- **Concurrencia**: Considera optimistic locking (campo `version` en `Factura`) para evitar conflictos.
- **Extensión**: Si necesitas validaciones adicionales (e.g., restricciones legales por país o validaciones de stock previas a emisión), añade specifications o intégralas en `InventarioService`.

Si deseas integrar estas validaciones con otras partes del sistema (e.g., sincronización con `NotaCredito` o implementación de `InventarioService.registrar_salida_fifo`), indícalos.





To consolidate the Domain-Driven Design (DDD) implementation for the Factura and NotaCredito aggregates, including the optimized validations for dates and stock, into a single cohesive Python project, we’ll organize the code into a modular structure with clear separation of concerns. The project will include all necessary entities, value objects, specifications, aggregates, services, and repositories, ensuring that:

Date Validations: As implemented previously, ensuring fecha_emision, fecha_caducidad, and fecha_autorizacion are valid for both Factura and NotaCredito.
Stock Validations: Integrated into FacturaAggregate to check sufficient stock before emitting a factura (via InventarioService), and into NotaCreditoAggregate to handle stock entries (reversing FIFO for returns).
Single Project: All code will be structured in a directory hierarchy, with shared specifications and reusable components, ready for integration with an ORM like SQLAlchemy (though we’ll keep persistence abstract for now).

The project will assume a MySQL database (based on the original schema) and include minimal dependencies (dataclasses, decimal, datetime). For stock validations, we’ll extend InventarioService to check stock availability (Inventario table) and handle FIFO logic (Lotes table) for Factura emissions and NotaCredito entries.



To implement stock validations for the NotaCreditoAggregate in the provided DDD project, we need to ensure that stock updates during the issuance of a NotaCredito are valid and consistent with the domain rules. Since a NotaCredito typically involves returning products to inventory (e.g., due to a refund or correction of a Factura), the stock validations will focus on ensuring that:

The products being returned (via LineaNotaCredito) do not exceed the quantities originally sold in the associated Factura.
The stock updates (via InventarioService) correctly increase the stock in the Inventario and create appropriate Lote entries for the returned items.
The validations are integrated into the NotaCreditoAggregate and NotaCreditoService, leveraging the existing InventarioService for stock operations.

We’ll reuse the existing project structure and extend the necessary components to include stock validations. Specifically, we’ll:

Update the nota_credito_specifications.py to include a stock-related specification (already partially covered by LineasValidasContraFactura, which checks quantities against the Factura).
Enhance NotaCreditoAggregate to validate stock operations during emitir.
Update NotaCreditoService to coordinate with InventarioService and ensure stock validations are applied before issuing the NotaCredito.
Ensure consistency with the FacturaAggregate stock validations and the InventarioService FIFO logic.

Modifications to Existing Code
1. Update nota_credito_specifications.py
The existing LineasValidasContraFactura specification already validates that the quantities in LineaNotaCredito do not exceed those in the associated Factura. We’ll keep this and add a new specification to ensure that the stock updates are feasible (e.g., ensuring the Inventario exists for the products and bodega). Since stock updates for NotaCredito are entries (not exits), the validation focuses on the existence of inventory records rather than sufficiency.


#### Changes and Optimizations
1. **New Specification**:
   - Added `InventarioExisteParaNotaCredito` to ensure that inventory records exist for all products in the `NotaCredito` lines and that they match the specified `bodega_id`. This prevents attempting to add stock to non-existent inventory records.
2. **Stock Validation in `NotaCreditoAggregate`**:
   - The `emitir` method now checks `InventarioExisteParaNotaCredito` before calling `InventarioService.registrar_entrada`.
   - This ensures that stock entries are only attempted if the inventory setup is valid.
3. **Integration with `InventarioService`**:
   - The `registrar_entrada` method in `InventarioService` (unchanged from the project) creates a new `Lote` for returned items and updates the `Inventario` stock, ensuring traceability via `MovimientoInventario`.
4. **Service-Level Validations**:
   - `LineasValidasContraFactura` ensures that the quantities in the `NotaCredito` do not exceed those in the `Factura`, acting as a stock-related validation at the business rule level.
   - `FechaEmisionPosteriorFactura` and `PlazoNotaCreditoValido` remain unchanged, ensuring temporal consistency.
5. **Error Handling**:
   - Failures in stock validation (e.g., missing inventory records) raise a `ValueError` with a clear message.
   - All validation errors are aggregated for better debugging.
6. **Consistency with `FacturaAggregate`**:
   - The stock validation for `NotaCredito` complements the `StockSuficienteParaFactura` in `FacturaAggregate`, ensuring that stock exits (for `Factura`) and entries (for `NotaCredito`) are both validated appropriately.

#### Notes
- **Persistencia**: Ensure that `NotaCreditoRepository` and `InventarioRepository` map the `Inventario` and `Lote` entities correctly with SQLAlchemy, using `Date` for `fecha_emision` and `fecha_caducidad`, and appropriate foreign keys for `id_bodega` and `id_producto`.
- **Testing**: Write unit tests for `InventarioExisteParaNotaCredito` (e.g., test with missing inventory records or mismatched `bodega_id`) and integration tests for `NotaCreditoService` with a mock database to verify stock updates.
- **Extensibility**: If additional stock rules are needed (e.g., checking product expiration dates in `Lote`), extend `InventarioService` or add new specifications.
- **Concurrency**: Use optimistic locking (e.g., a `version` field in `Inventario`) to prevent race conditions during stock updates.
- **Event Sourcing**: Consider emitting a `NotaCreditoEmitida` event after successful issuance to notify other systems (e.g., accounting).

The existing project structure remains intact, and these changes integrate seamlessly with the previously provided code for `FacturaAggregate` and other components. If you need further extensions (e.g., implementing `InventarioRepository` with SQLAlchemy or adding more complex stock rules), let me know!









To add unit tests for the stock validations in the FacturaAggregate and NotaCreditoAggregate, we’ll focus on testing the stock-related specifications (StockSuficienteParaFactura and InventarioExisteParaNotaCredito) and their integration within the aggregates’ emitir methods. The tests will verify that:

FacturaAggregate: The StockSuficienteParaFactura specification correctly validates stock availability before emitting a factura, ensuring quantities requested in LineaFactura do not exceed available stock in Inventario.
NotaCreditoAggregate: The InventarioExisteParaNotaCredito specification ensures inventory records exist for the products and bodega before processing stock entries, and LineasValidasContraFactura validates quantities against the associated Factura.
InventarioService: The registrar_salida_fifo and registrar_entrada methods correctly handle stock updates and generate appropriate MovimientoInventario records.

We’ll use Python’s unittest framework with unittest.mock to mock dependencies like InventarioRepository, LoteRepository, and FacturaRepository. The tests will be organized in a tests/ directory within the project structure, ensuring modularity and maintainability.
Updated Project Structure



facturacion_ddd/
├── domain/
│   ├── entities/
│   │   ├── factura.py
│   │   ├── linea_factura.py
│   │   ├── totales_factura.py
│   │   ├── nota_credito.py
│   │   ├── linea_nota_credito.py
│   │   ├── totales_nota_credito.py
│   │   ├── producto.py
│   │   ├── inventario.py
│   │   ├── lote.py
│   │   ├── movimiento_inventario.py
│   ├── value_objects/
│   │   ├── direccion.py
│   │   ├── ruc.py
│   │   ├── forma_pago.py
│   │   ├── motivo_modificacion.py
│   │   ├── precio.py
│   ├── specifications/
│   │   ├── factura_specifications.py
│   │   ├── nota_credito_specifications.py
│   │   ├── inventario_specifications.py
│   ├── aggregates/
│   │   ├── factura_aggregate.py
│   │   ├── nota_credito_aggregate.py
│   ├── services/
│   │   ├── factura_service.py
│   │   ├── nota_credito_service.py
│   │   ├── inventario_service.py
│   ├── repositories/
│   │   ├── factura_repository.py
│   │   ├── nota_credito_repository.py
│   │   ├── inventario_repository.py
│   │   ├── lote_repository.py
│   │   ├── producto_repository.py
├── tests/
│   ├── test_factura_aggregate.py
│   ├── test_nota_credito_aggregate.py
│   ├── test_inventario_service.py
├── infrastructure/
│   └── persistence/
│       ├── sql_repository.py
└── application/
    └── main.py
Unit Tests for Stock Valid





Unit Tests for Stock Validations
Below are the unit tests for the stock validations, covering FacturaAggregate, NotaCreditoAggregate, and InventarioService. Each test file is wrapped in an <xaiArtifact> tag with a unique UUID, as required.
1. Test FacturaAggregate Stock Validations
This test suite verifies the StockSuficienteParaFactura specification and its integration in FacturaAggregate.emitir.




### Explanation of Tests
1. **TestFacturaAggregate**:
   - `test_stock_suficiente_para_factura`: Verifies that a factura can be emitted when sufficient stock is available, checking that `InventarioService.registrar_salida_fifo` is called correctly and returns `MovimientoInventario`.
   - `test_stock_insuficiente_raises_error`: Ensures that attempting to emit a factura with insufficient stock raises a `ValueError`.
   - `test_no_inventario_raises_error`: Tests that a missing inventory record triggers a `ValueError`.

2. **TestNotaCreditoAggregate**:
   - `test_inventario_existe_para_nota_credito`: Confirms that a nota de crédito can be emitted when inventory records exist, verifying that `InventarioService.registrar_entrada` is called and returns `MovimientoInventario`.
   - `test_inventario_no_existe_raises_error`: Ensures that a missing inventory record raises a `ValueError`.
   - `test_lineas_validas_contra_factura`: Validates that `LineasValidasContraFactura` passes when the nota de crédito quantities are within the factura’s limits.
   - `test_lineas_invalidas_contra_factura_raises_error`: Checks that exceeding the factura’s quantities fails the `LineasValidasContraFactura` validation.

3. **TestInventarioService**:
   - `test_registrar_salida_fifo_suficiente`: Verifies that `registrar_salida_fifo` correctly processes stock exits using FIFO, updating `Lote` and `Inventario`.
   - `test_registrar_salida_fifo_insuficiente`: Ensures that insufficient stock in FIFO logic raises a `ValueError`.
   - `test_registrar_entrada`: Confirms that `registrar_entrada` correctly updates stock and creates a new `Lote` for returned items.
   - `test_registrar_entrada_no_inventario`: Tests that a missing inventory record raises a `ValueError`.

### Running the Tests
To run the tests, place the test files in the `tests/` directory and execute:
```bash
python -m unittest discover tests

