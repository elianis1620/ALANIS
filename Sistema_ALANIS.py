"""
PROYECTO FASE 4 - PROGRAMACION (UNAD)
Sistema Integral de Gestion de Clientes, Servicios y Reservas
Empresa: Software FJ

Requisitos incluidos:
- Programacion orientada a objetos: abstraccion, herencia, encapsulacion y polimorfismo.
- Clases abstractas Entidad y Servicio.
- Cliente con validaciones.
- Tres servicios especializados.
- Reservas con confirmacion, cancelacion y procesamiento.
- Calculo de costos con parametros opcionales (impuestos y descuentos).
- Excepciones personalizadas y manejo try/except/else/finally.
- Registro de eventos y errores en software_fj.log.
- Diez o mas operaciones de demostracion.
- Sin bases de datos: se utilizan objetos y listas en memoria.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import logging


# ------------------------- CONFIGURACION DE LOGS -------------------------

logging.basicConfig(
    filename="software_fj.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)


# ------------------------- EXCEPCIONES PERSONALIZADAS --------------------

class ErrorSistema(Exception):
    """Excepcion base del sistema Software FJ."""


class DatoInvalidoError(ErrorSistema):
    """Se genera cuando un dato no cumple las validaciones."""


class ServicioNoDisponibleError(ErrorSistema):
    """Se genera cuando un servicio no esta disponible."""


class ReservaError(ErrorSistema):
    """Se genera cuando una operacion de reserva no es permitida."""


# ------------------------- CLASE ABSTRACTA ENTIDAD -----------------------

class Entidad(ABC):
    def __init__(self, identificacion):
        if not identificacion or not str(identificacion).strip():
            raise DatoInvalidoError("La identificacion es obligatoria.")
        self._identificacion = str(identificacion).strip()

    @property
    def identificacion(self):
        return self._identificacion

    @abstractmethod
    def describir(self):
        pass


# ------------------------- CLASE CLIENTE ---------------------------------

class Cliente(Entidad):
    def __init__(self, identificacion, nombre, correo, telefono):
        super().__init__(identificacion)

        if not nombre or len(nombre.strip()) < 3:
            raise DatoInvalidoError("El nombre debe tener minimo 3 caracteres.")
        if "@" not in correo or "." not in correo:
            raise DatoInvalidoError("El correo electronico no es valido.")
        if not str(telefono).isdigit() or len(str(telefono)) < 7:
            raise DatoInvalidoError("El telefono debe contener minimo 7 digitos.")

        self.__nombre = nombre.strip()
        self.__correo = correo.strip().lower()
        self.__telefono = str(telefono)

    @property
    def nombre(self):
        return self.__nombre

    @property
    def correo(self):
        return self.__correo

    def describir(self):
        return f"Cliente: {self.__nombre} | ID: {self.identificacion}"

    def __str__(self):
        return f"{self.__nombre} ({self.identificacion})"


# ------------------------- CLASE ABSTRACTA SERVICIO ----------------------

class Servicio(ABC):
    def __init__(self, codigo, nombre, tarifa_hora, disponible=True):
        if not codigo or not nombre:
            raise DatoInvalidoError("El codigo y el nombre del servicio son obligatorios.")
        if not isinstance(tarifa_hora, (int, float)) or tarifa_hora <= 0:
            raise DatoInvalidoError("La tarifa debe ser un numero mayor que cero.")

        self.codigo = str(codigo)
        self.nombre = nombre
        self.tarifa_hora = float(tarifa_hora)
        self.disponible = bool(disponible)

    def validar(self, duracion):
        if not self.disponible:
            raise ServicioNoDisponibleError(
                f"El servicio '{self.nombre}' no se encuentra disponible."
            )
        # Encadenamiento de excepciones: se conserva la causa original
        # cuando no es posible convertir la duracion a un numero.
        try:
            duracion = float(duracion)
        except (TypeError, ValueError) as error:
            raise DatoInvalidoError(
                "La duracion debe ser un valor numerico."
            ) from error
        if duracion <= 0:
            raise DatoInvalidoError("La duracion debe ser mayor que cero.")

    # Una misma operacion acepta distintas variantes de calculo:
    # costo(duracion), costo(duracion, impuesto) o costo(duracion, impuesto, descuento).
    def calcular_costo(self, duracion, impuesto=0.19, descuento=0):
        self.validar(duracion)
        if not 0 <= impuesto <= 1:
            raise DatoInvalidoError("El impuesto debe estar entre 0 y 1.")
        if not 0 <= descuento <= 1:
            raise DatoInvalidoError("El descuento debe estar entre 0 y 1.")

        subtotal = self.tarifa_hora * duracion
        subtotal_con_descuento = subtotal * (1 - descuento)
        return round(subtotal_con_descuento * (1 + impuesto), 2)

    @abstractmethod
    def describir_servicio(self):
        pass

    @abstractmethod
    def validar_parametros(self, duracion):
        pass


# ------------------------- SERVICIOS ESPECIALIZADOS ----------------------

class ReservaSala(Servicio):
    def __init__(self, codigo, tarifa_hora, capacidad, disponible=True):
        super().__init__(codigo, "Reserva de sala", tarifa_hora, disponible)
        if not isinstance(capacidad, int) or capacidad <= 0:
            raise DatoInvalidoError("La capacidad de la sala debe ser un entero positivo.")
        self.capacidad = capacidad

    def validar_parametros(self, duracion):
        self.validar(duracion)

    def describir_servicio(self):
        return f"{self.nombre} | Capacidad: {self.capacidad} personas"


class AlquilerEquipo(Servicio):
    def __init__(self, codigo, tarifa_hora, tipo_equipo, disponible=True):
        super().__init__(codigo, "Alquiler de equipos", tarifa_hora, disponible)
        if not tipo_equipo or not tipo_equipo.strip():
            raise DatoInvalidoError("Debe indicar el tipo de equipo.")
        self.tipo_equipo = tipo_equipo

    def validar_parametros(self, duracion):
        self.validar(duracion)

    def describir_servicio(self):
        return f"{self.nombre} | Equipo: {self.tipo_equipo}"


class AsesoriaEspecializada(Servicio):
    def __init__(self, codigo, tarifa_hora, especialidad, disponible=True):
        super().__init__(codigo, "Asesoria especializada", tarifa_hora, disponible)
        if not especialidad or not especialidad.strip():
            raise DatoInvalidoError("Debe indicar la especialidad de la asesoria.")
        self.especialidad = especialidad

    def validar_parametros(self, duracion):
        self.validar(duracion)

    def describir_servicio(self):
        return f"{self.nombre} | Especialidad: {self.especialidad}"


# ------------------------- CLASE RESERVA ---------------------------------

class Reserva:
    contador = 0

    def __init__(self, cliente, servicio, duracion):
        if not isinstance(cliente, Cliente):
            raise DatoInvalidoError("La reserva requiere un cliente valido.")
        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError("La reserva requiere un servicio valido.")

        servicio.validar_parametros(duracion)
        Reserva.contador += 1
        self.codigo = f"R-{Reserva.contador:03d}"
        self.cliente = cliente
        self.servicio = servicio
        self.duracion = float(duracion)
        self.estado = "Pendiente"
        self.total = 0.0

    def confirmar(self, impuesto=0.19, descuento=0):
        if self.estado != "Pendiente":
            raise ReservaError("Solo se pueden confirmar reservas pendientes.")
        try:
            self.total = self.servicio.calcular_costo(
                self.duracion, impuesto, descuento
            )
            self.estado = "Confirmada"
            logging.info("Reserva %s confirmada. Total: %.2f", self.codigo, self.total)
            return self.total
        except ErrorSistema:
            logging.exception("Error al confirmar la reserva %s", self.codigo)
            raise
        finally:
            logging.info("Finalizo el intento de confirmacion de %s", self.codigo)

    def cancelar(self):
        if self.estado == "Cancelada":
            raise ReservaError("La reserva ya se encuentra cancelada.")
        if self.estado == "Procesada":
            raise ReservaError("No se puede cancelar una reserva procesada.")
        self.estado = "Cancelada"
        logging.info("Reserva %s cancelada.", self.codigo)

    def procesar(self):
        if self.estado != "Confirmada":
            raise ReservaError("La reserva debe estar confirmada antes de procesarse.")
        self.estado = "Procesada"
        logging.info("Reserva %s procesada.", self.codigo)

    def __str__(self):
        return (
            f"{self.codigo} | {self.cliente.nombre} | "
            f"{self.servicio.nombre} | {self.duracion:g} horas | "
            f"Estado: {self.estado} | Total: ${self.total:,.2f}"
        )


# ------------------------- SISTEMA DE GESTION ----------------------------

class SistemaSoftwareFJ:
    def __init__(self):
        self.clientes = []
        self.servicios = []
        self.reservas = []

    def registrar_cliente(self, cliente):
        if any(c.identificacion == cliente.identificacion for c in self.clientes):
            raise DatoInvalidoError("Ya existe un cliente con esa identificacion.")
        self.clientes.append(cliente)
        logging.info("Cliente registrado: %s", cliente.identificacion)
        return cliente

    def agregar_servicio(self, servicio):
        if any(s.codigo == servicio.codigo for s in self.servicios):
            raise DatoInvalidoError("Ya existe un servicio con ese codigo.")
        self.servicios.append(servicio)
        logging.info("Servicio agregado: %s", servicio.codigo)
        return servicio

    def crear_reserva(self, cliente, servicio, duracion):
        reserva = Reserva(cliente, servicio, duracion)
        self.reservas.append(reserva)
        logging.info("Reserva creada: %s", reserva.codigo)
        return reserva

    def mostrar_informacion(self):
        print("\n========== CLIENTES ==========")
        for cliente in self.clientes:
            print(cliente.describir())

        print("\n========== SERVICIOS ==========")
        for servicio in self.servicios:
            # Polimorfismo: cada servicio responde con su propia descripcion.
            print(servicio.describir_servicio())

        print("\n========== RESERVAS ==========")
        for reserva in self.reservas:
            print(reserva)


# ------------------------- PRUEBAS: 10 O MAS OPERACIONES -----------------

def ejecutar_demostracion():
    sistema = SistemaSoftwareFJ()

    print("=" * 65)
    print(" SISTEMA INTEGRAL DE GESTION - SOFTWARE FJ")
    print("=" * 65)

    operaciones = 0

    def ejecutar(titulo, accion):
        nonlocal operaciones
        operaciones += 1
        print(f"\nOperacion {operaciones}: {titulo}")
        try:
            resultado = accion()
        except ErrorSistema as error:
            print(f"[ERROR CONTROLADO] {error}")
            logging.error("Operacion %s - %s: %s", operaciones, titulo, error)
        except Exception as error:
            print(f"[ERROR INESPERADO] {error}")
            logging.exception("Error inesperado en operacion %s", operaciones)
        else:
            if resultado is not None:
                print(f"[OK] {resultado}")
            else:
                print("[OK] Operacion realizada.")
        finally:
            print("[FIN] La aplicacion continua en ejecucion.")

    # 1. Registro valido de cliente.
    ejecutar(
        "Registrar cliente valido",
        lambda: sistema.registrar_cliente(
            Cliente("1001", "Carlos Ramirez", "carlos@email.com", "3101234567")
        )
    )

    # 2. Registro de un segundo cliente.
    ejecutar(
        "Registrar segundo cliente",
        lambda: sistema.registrar_cliente(
            Cliente("1002", "Laura Gomez", "laura@email.com", "3207654321")
        )
    )

    # 3. Intento de registro invalido.
    ejecutar(
        "Registrar cliente con correo invalido",
        lambda: sistema.registrar_cliente(
            Cliente("1003", "Pedro Lopez", "correo_invalido", "3111234567")
        )
    )

    # 4. Crear servicio de sala.
    ejecutar(
        "Crear servicio de reserva de sala",
        lambda: sistema.agregar_servicio(
            ReservaSala("S01", 50000, 20)
        )
    )

    # 5. Crear servicio de alquiler de equipos.
    ejecutar(
        "Crear servicio de alquiler de equipos",
        lambda: sistema.agregar_servicio(
            AlquilerEquipo("S02", 30000, "Video beam")
        )
    )

    # 6. Crear servicio de asesoria.
    ejecutar(
        "Crear servicio de asesoria especializada",
        lambda: sistema.agregar_servicio(
            AsesoriaEspecializada("S03", 80000, "Redes y telecomunicaciones")
        )
    )

    # 7. Intento de crear servicio con tarifa invalida.
    ejecutar(
        "Crear servicio con tarifa negativa",
        lambda: sistema.agregar_servicio(
            AlquilerEquipo("S04", -1000, "Computador")
        )
    )

    cliente_1 = sistema.clientes[0]
    sala = sistema.servicios[0]
    equipo = sistema.servicios[1]
    asesoria = sistema.servicios[2]

    # 8. Crear una reserva correcta.
    reserva_1 = None
    def crear_reserva_1():
        nonlocal reserva_1
        reserva_1 = sistema.crear_reserva(cliente_1, sala, 2)
        return reserva_1
    ejecutar("Crear reserva de sala", crear_reserva_1)

    # 9. Confirmar reserva con impuesto y descuento.
    ejecutar(
        "Confirmar reserva con descuento del 10%",
        lambda: f"Total: ${reserva_1.confirmar(0.19, 0.10):,.2f}"
    )

    # 10. Procesar reserva confirmada.
    ejecutar("Procesar reserva confirmada", reserva_1.procesar)

    # 11. Intentar cancelar una reserva ya procesada.
    ejecutar("Intentar cancelar reserva procesada", reserva_1.cancelar)

    # 12. Crear una reserva con duracion invalida.
    ejecutar(
        "Crear reserva con duracion cero",
        lambda: sistema.crear_reserva(cliente_1, equipo, 0)
    )

    # 13. Crear y cancelar una reserva pendiente.
    reserva_2 = None
    def crear_reserva_2():
        nonlocal reserva_2
        reserva_2 = sistema.crear_reserva(cliente_1, equipo, 1.5)
        return reserva_2
    ejecutar("Crear reserva de equipo", crear_reserva_2)
    ejecutar("Cancelar reserva pendiente", reserva_2.cancelar)

    # 14. Intentar reservar un servicio no disponible.
    servicio_no_disponible = AsesoriaEspecializada(
        "S05", 60000, "Ciberseguridad", disponible=False
    )
    ejecutar(
        "Intentar reservar servicio no disponible",
        lambda: sistema.crear_reserva(cliente_1, servicio_no_disponible, 1)
    )

    # 15. Crear y confirmar una asesoria.
    reserva_3 = None
    def crear_reserva_3():
        nonlocal reserva_3
        reserva_3 = sistema.crear_reserva(cliente_1, asesoria, 1)
        return reserva_3
    ejecutar("Crear reserva de asesoria", crear_reserva_3)
    ejecutar("Confirmar reserva de asesoria", reserva_3.confirmar)

    # 16. Intentar confirmar nuevamente una reserva confirmada.
    ejecutar("Intentar confirmar dos veces la misma reserva", reserva_3.confirmar)

    print("\n" + "=" * 65)
    print("RESUMEN FINAL")
    print("=" * 65)
    print(f"Operaciones ejecutadas: {operaciones}")
    print(f"Clientes registrados: {len(sistema.clientes)}")
    print(f"Servicios registrados: {len(sistema.servicios)}")
    print(f"Reservas creadas: {len(sistema.reservas)}")
    sistema.mostrar_informacion()
    print("\nLos eventos y errores se guardaron en el archivo software_fj.log")
    print("La demostracion finalizo sin detener la aplicacion.")



# ------------------------- MENU INTERACTIVO ------------------------------

def leer_entero(mensaje):
    try:
        return int(input(mensaje).strip())
    except ValueError as error:
        raise DatoInvalidoError("Debe ingresar un numero entero.") from error


def leer_decimal(mensaje):
    try:
        return float(input(mensaje).strip().replace(",", "."))
    except ValueError as error:
        raise DatoInvalidoError("Debe ingresar un valor numerico.") from error


def menu_interactivo():
    sistema = SistemaSoftwareFJ()

    print("\n" + "=" * 65)
    print(" SISTEMA INTEGRAL DE GESTION - SOFTWARE FJ")
    print("=" * 65)
    print("Bienvenido. Los datos se almacenan temporalmente en memoria.")
    print("El archivo software_fj.log guardara los eventos y errores.")

    while True:
        print("\n--------------- MENU PRINCIPAL ---------------")
        print("1. Registrar cliente")
        print("2. Crear servicio")
        print("3. Realizar reserva")
        print("4. Confirmar reserva")
        print("5. Cancelar reserva")
        print("6. Procesar reserva")
        print("7. Ver clientes")
        print("8. Ver servicios")
        print("9. Ver reservas")
        print("10. Ejecutar demostracion automatica (16 operaciones)")
        print("0. Salir")

        try:
            opcion = leer_entero("Seleccione una opcion: ")

            if opcion == 1:
                print("\n--- REGISTRO DE CLIENTE ---")
                identificacion = input("Identificacion: ").strip()
                nombre = input("Nombre completo: ").strip()
                correo = input("Correo electronico: ").strip()
                telefono = input("Telefono: ").strip()
                cliente = Cliente(identificacion, nombre, correo, telefono)
                sistema.registrar_cliente(cliente)
                print("[OK] Cliente registrado correctamente.")

            elif opcion == 2:
                print("\n--- CREACION DE SERVICIO ---")
                print("1. Reserva de sala")
                print("2. Alquiler de equipos")
                print("3. Asesoria especializada")
                tipo = leer_entero("Tipo de servicio: ")
                codigo = input("Codigo del servicio: ").strip()
                tarifa = leer_decimal("Tarifa por hora: $")

                if tipo == 1:
                    capacidad = leer_entero("Capacidad de la sala: ")
                    servicio = ReservaSala(codigo, tarifa, capacidad)
                elif tipo == 2:
                    equipo = input("Tipo de equipo: ").strip()
                    servicio = AlquilerEquipo(codigo, tarifa, equipo)
                elif tipo == 3:
                    especialidad = input("Especialidad de la asesoria: ").strip()
                    servicio = AsesoriaEspecializada(codigo, tarifa, especialidad)
                else:
                    raise DatoInvalidoError("Tipo de servicio no valido.")

                sistema.agregar_servicio(servicio)
                print("[OK] Servicio creado correctamente.")

            elif opcion == 3:
                print("\n--- CREAR RESERVA ---")
                if not sistema.clientes:
                    raise ReservaError("Primero debe registrar al menos un cliente.")
                if not sistema.servicios:
                    raise ReservaError("Primero debe crear al menos un servicio.")

                print("Clientes disponibles:")
                for i, cliente in enumerate(sistema.clientes, start=1):
                    print(f"{i}. {cliente.describir()}")

                indice_cliente = leer_entero("Seleccione el numero del cliente: ") - 1
                if indice_cliente < 0 or indice_cliente >= len(sistema.clientes):
                    raise DatoInvalidoError("El cliente seleccionado no existe.")

                print("\nServicios disponibles:")
                for i, servicio in enumerate(sistema.servicios, start=1):
                    estado = "Disponible" if servicio.disponible else "No disponible"
                    print(f"{i}. {servicio.describir_servicio()} | ${servicio.tarifa_hora:,.2f}/hora | {estado}")

                indice_servicio = leer_entero("Seleccione el numero del servicio: ") - 1
                if indice_servicio < 0 or indice_servicio >= len(sistema.servicios):
                    raise DatoInvalidoError("El servicio seleccionado no existe.")

                duracion = leer_decimal("Duracion en horas: ")
                reserva = sistema.crear_reserva(
                    sistema.clientes[indice_cliente],
                    sistema.servicios[indice_servicio],
                    duracion
                )
                print(f"[OK] Reserva creada: {reserva.codigo} (estado: {reserva.estado}).")

            elif opcion == 4:
                codigo = input("Codigo de la reserva a confirmar: ").strip()
                reserva = next((r for r in sistema.reservas if r.codigo == codigo), None)
                if reserva is None:
                    raise ReservaError("No se encontro la reserva indicada.")
                impuesto = leer_decimal("Impuesto (por ejemplo 0.19): ")
                descuento = leer_decimal("Descuento (por ejemplo 0.10, sin porcentaje): ")
                total = reserva.confirmar(impuesto, descuento)
                print(f"[OK] Reserva confirmada. Total: ${total:,.2f}")

            elif opcion == 5:
                codigo = input("Codigo de la reserva a cancelar: ").strip()
                reserva = next((r for r in sistema.reservas if r.codigo == codigo), None)
                if reserva is None:
                    raise ReservaError("No se encontro la reserva indicada.")
                reserva.cancelar()
                print("[OK] Reserva cancelada.")

            elif opcion == 6:
                codigo = input("Codigo de la reserva a procesar: ").strip()
                reserva = next((r for r in sistema.reservas if r.codigo == codigo), None)
                if reserva is None:
                    raise ReservaError("No se encontro la reserva indicada.")
                reserva.procesar()
                print("[OK] Reserva procesada.")

            elif opcion == 7:
                print("\n--- CLIENTES REGISTRADOS ---")
                if not sistema.clientes:
                    print("No hay clientes registrados.")
                for cliente in sistema.clientes:
                    print(cliente.describir(), "|", cliente.correo)

            elif opcion == 8:
                print("\n--- SERVICIOS REGISTRADOS ---")
                if not sistema.servicios:
                    print("No hay servicios registrados.")
                for servicio in sistema.servicios:
                    print(
                        servicio.describir_servicio(),
                        f"| Codigo: {servicio.codigo}",
                        f"| Tarifa: ${servicio.tarifa_hora:,.2f}/hora"
                    )

            elif opcion == 9:
                print("\n--- RESERVAS REGISTRADAS ---")
                if not sistema.reservas:
                    print("No hay reservas registradas.")
                for reserva in sistema.reservas:
                    print(reserva)

            elif opcion == 10:
                print("\nSe ejecutara la demostracion automatica en una instancia independiente.")
                ejecutar_demostracion()

            elif opcion == 0:
                print("\nGracias por utilizar Software FJ.")
                print("Los eventos y errores quedaron registrados en software_fj.log.")
                break

            else:
                raise DatoInvalidoError("Opcion no valida. Seleccione una opcion del menu.")

        except ErrorSistema as error:
            print(f"\n[ERROR CONTROLADO] {error}")
            logging.error("Error en el menu interactivo: %s", error)
        except Exception as error:
            print(f"\n[ERROR INESPERADO] {error}")
            logging.exception("Error inesperado en el menu interactivo")
        finally:
            print("\nLa aplicacion sigue disponible.")


# ------------------------- PROGRAMA PRINCIPAL ----------------------------

if __name__ == "__main__":
    try:
        menu_interactivo()
    except KeyboardInterrupt:
        print("\nPrograma interrumpido por el usuario.")
        logging.warning("El usuario interrumpio el programa.")
    except Exception as error:
        logging.exception("Error critico en el programa principal")
        print(f"Se presento un error general: {error}")
    finally:
        print("\nPrograma finalizado.")
