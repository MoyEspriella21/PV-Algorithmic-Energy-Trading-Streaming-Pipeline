import pvlib
import pandas as pd
import numpy as np
import requests
import time
import json
from pvlib.location import Location
from pvlib.temperature import TEMPERATURE_MODEL_PARAMETERS

# --- CONFIGURACIÓN DEL SISTEMA ---
# Ubicación: Badajoz, España
LATITUDE = 38.8786
LONGITUDE = -6.9706
TZ = 'Europe/Madrid'

# Modelos (Búsqueda en bases de datos SAM)
MODULE_NAME = 'Canadian_Solar_Inc__CS3W_400P' # Modelo 400W aproximado
INVERTER_NAME = 'SMA_America__SC800CP_US__with_ABB_EcoDry_Ultra_transformer_' # SMA Sunny Central

def obtener_datos_meteorologicos():
    """Obtiene datos en tiempo real de Open-Meteo API para Badajoz."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LATITUDE}&longitude={LONGITUDE}&current=temperature_2m,wind_speed_10m,direct_normal_irradiance,diffuse_radiation&timezone=auto"
    try:
        response = requests.get(url)
        data = response.json()['current']
        return {
            'temp_air': data['temperature_2m'],
            'wind_speed': data['wind_speed_10m'] / 3.6, # Convertir km/h a m/s
            'dni': data['direct_normal_irradiance'],
            'dhi': data['diffuse_radiation']
        }
    except Exception as e:
        print(f"Error obteniendo meteorología: {e}")
        return None

def obtener_precio_mercado():
    """Obtiene el precio del mercado diario (OMIE) desde ESIOS."""
    # Nota: ESIOS requiere un token x-api-key para acceso profesional.
    # Se usa el indicador 1001 (Precio mercado diario)
    token = "TU_TOKEN_ESIOS" # Placeholder
    headers = {'Accept': 'application/json; application/vnd.esios-api-v1+json',
               'Content-Type': 'application/json',
               'x-api-key': token}
    url = "https://api.esios.ree.es/indicators/1001"
    
    try:
        # Intentamos obtener el precio. Si no hay token, devolvemos un valor base/error manejado.
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            # Tomamos el valor más reciente
            val = response.json()['indicator']['values'][-1]['value']
            return val
        else:
            # Fallback para demostración si no hay token
            return 60.5 # Valor dummy en €/MWh
    except Exception:
        return 60.5

def calcular_generacion_actual(timestamp, dni, dhi, temp_air, wind_speed):
    """Lógica matemática core del Gemelo Digital."""
    location = Location(LATITUDE, LONGITUDE, tz=TZ)
    solar_position = location.get_solarposition(timestamp)
    
    # Cargar Bases de Datos
    cec_modules = pvlib.pvsystem.retrieve_sam('CECMod')
    sandia_inverters = pvlib.pvsystem.retrieve_sam('SandiaInverter')
    
    module = cec_modules[MODULE_NAME]
    inverter = sandia_inverters[INVERTER_NAME]
    
    # 1. Irradiancia en el Plano (POA)
    dni_extra = pvlib.irradiance.get_extra_radiation(timestamp)
    # GHI simplificado
    ghi = dni * np.cos(np.radians(solar_position['zenith'])) + dhi
    
    poa = pvlib.irradiance.get_total_irradiance(
        surface_tilt=30,
        surface_azimuth=180,
        solar_zenith=solar_position['apparent_zenith'],
        solar_azimuth=solar_position['azimuth'],
        dni=dni,
        ghi=ghi,
        dhi=dhi,
        dni_extra=dni_extra
    )
    
    # Early exit if there is no irradiance (nighttime)
    poa_global = float(poa['poa_global'].iloc[0] if isinstance(poa['poa_global'], pd.Series) else poa['poa_global'])
    if poa_global < 0.1:
        return {
            'poa_global': round(poa_global, 2),
            'cell_temperature': round(float(temp_air), 2),
            'ac_power_w': 0.0
        }
    
    # 2. Modelo Térmico
    temp_params = TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass']
    cell_temp = pvlib.temperature.sapm_cell(
        poa['poa_global'], temp_air, wind_speed, **temp_params
    )
    
    # 3. Modelo DC (CEC)
    cec_params = pvlib.pvsystem.calcparams_cec(
        effective_irradiance=poa['poa_global'],
        temp_cell=cell_temp,
        alpha_sc=module['alpha_sc'],
        a_ref=module['a_ref'],
        I_L_ref=module['I_L_ref'],
        I_o_ref=module['I_o_ref'],
        R_sh_ref=module['R_sh_ref'],
        R_s=module['R_s'],
        Adjust=module['Adjust']
    )
    iv_values = pvlib.pvsystem.singlediode(*cec_params)
    
    # 4. Modelo AC (Sandia)
    p_ac = pvlib.inverter.sandia(iv_values['v_mp'], iv_values['p_mp'], inverter)
    
    return {
        'poa_global': round(float(poa['poa_global'].iloc[0] if isinstance(poa['poa_global'], pd.Series) else poa['poa_global']), 2),
        'cell_temperature': round(float(cell_temp.iloc[0] if isinstance(cell_temp, pd.Series) else cell_temp), 2),
        'ac_power_w': round(max(0.0, float(p_ac.iloc[0] if isinstance(p_ac, pd.Series) else p_ac)), 2)
    }

def main():
    print(f"Iniciando Gemelo Digital para Badajoz ({LATITUDE}, {LONGITUDE})...")
    
    while True:
        ahora = pd.Timestamp.now(tz=TZ)
        
        # 1. Obtener datos externos
        meteo = obtener_datos_meteorologicos()
        precio = obtener_precio_mercado()
        
        if meteo:
            # 2. Ejecutar cálculo
            generacion = calcular_generacion_actual(
                ahora, 
                meteo['dni'], 
                meteo['dhi'], 
                meteo['temp_air'], 
                meteo['wind_speed']
            )
            
            # 3. Consolidar resultado
            output = {
                "timestamp": ahora.isoformat(),
                "location": "Badajoz, ES",
                "weather": meteo,
                "generation": generacion,
                "market_price_eur_mwh": precio,
                "estimated_revenue_eur": round((generacion['ac_power_w'] / 1e6) * precio, 6)
            }
            
            # 4. Imprimir como JSON
            print(json.dumps(output, indent=None))
        
        # Esperar 60 segundos
        time.sleep(60)

if __name__ == "__main__":
    main()
