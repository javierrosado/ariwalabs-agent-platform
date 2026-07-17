# Project Context

## AriwaLabs

AriwaLabs es una empresa peruana de capacitacion y consultoria en inteligencia
artificial. Su prioridad inicial es vender capacitaciones en IA y construir una
comunidad que permita identificar oportunidades futuras de consultoria.

El director, Javier, es el unico operador y aprobador de los agentes durante el
MVP.

## Oferta formativa inicial

La oferta inicial tiene tres niveles secuenciales:

- Nivel Basico.
- Nivel Intermedio.
- Nivel Avanzado.

Cada nivel depende del anterior. Las caracteristicas comerciales previstas son:

- duracion maxima de 48 horas por nivel;
- modalidad hibrida;
- clases en vivo;
- certificado;
- precio estimado de S/ 500 por nivel;
- promocion: tres personas pagan y una cuarta participa sin costo;
- becas disponibles;
- sin pago fraccionado inicialmente;
- convenios universitarios;
- programas corporativos;
- programa de referidos.

El nivel avanzado se enfoca en implementar agentes de IA para acelerar el ciclo
de desarrollo de software usando demos para telco, banca y retail.

## Segmentos prioritarios

Los segmentos iniciales son:

- estudiantes universitarios;
- recien egresados;
- profesionales con experiencia en Ingenieria de Sistemas, Ingenieria de
  Software, Ciencias de la Computacion o carreras afines.

## Flywheel capacitacion-consultoria

La estrategia de crecimiento es:

1. captar prospectos;
2. convertirlos en alumnos;
3. llevarlos por los tres niveles;
4. certificarlos;
5. desarrollar comunidad;
6. identificar voluntariamente las empresas donde trabajan;
7. detectar senales de necesidades de IA;
8. generar oportunidades potenciales de consultoria;
9. someter cada oportunidad a revision del director;
10. convertir proyectos exitosos en conocimiento y casos reutilizables.

La capacitacion no es solo una linea de ingresos; es el canal inicial para
desarrollar comunidad, confianza, datos consentidos y posibles oportunidades
corporativas.

## Modelo operativo

- Desarrollo local en VS Code.
- Python con entorno virtual local.
- Codex como asistente de ingenieria.
- GitHub como fuente de verdad tecnica.
- Airtable como sistema operacional inicial.
- Runtime local con persistencia JSON durante el esqueleto del MVP.
- Aprobacion humana obligatoria para acciones de impacto externo.

## Integraciones previstas

Iniciales:

- OpenAI API mediante Model Gateway.
- Airtable mediante Airtable Adapter.
- Airtable Forms para captacion.
- GitHub para codigo, agentes, prompts, schemas, politicas, pruebas y docs.

Posteriores:

- WhatsApp Business Platform mediante adapter o automatizacion.
- Email transaccional.
- Google Calendar o Microsoft Calendar.
- Plataforma de publicacion como Metricool, Buffer o equivalente.
- LinkedIn inicialmente con publicacion manual.
- Pasarela de pago en fase posterior.
- Azure o Microsoft Foundry en fase posterior.

## Restricciones tecnicas y de gobierno

- No usar SQLite en el MVP.
- No introducir contenedores durante la primera etapa.
- No acoplar skills a modelos concretos.
- No permitir llamadas directas de skills a APIs externas.
- No versionar secretos ni datos sensibles de alumnos o empresas.
- No registrar oportunidades corporativas sin aprobacion.
- No inventar metricas, casos de exito, clientes ni claims.

## Prioridades actuales

1. Convertir el esqueleto del framework en componentes reales: registries,
   workflow, approvals, artifacts y audit completo.
2. Endurecer schemas de skills y handoffs.
3. Implementar Airtable Adapter y diseno de tablas.
4. Implementar Model Gateway con perfiles logicos y structured outputs.
5. Agregar pruebas de regresion antes de crear nuevos agentes.
