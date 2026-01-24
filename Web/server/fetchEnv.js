// fetchEnv.js
const axios = require('axios');
const http = require('http');
const https = require('https');

// --- 1. CONFIGURATION ---
// Force IPv4 to fix Node connection issues (ETIMEDOUT fix)
const httpAgent = new http.Agent({ family: 4 });
const httpsAgent = new https.Agent({ family: 4 });

// In-Memory Cache to store weather results for 10 minutes
// Prevents "Too Many Requests" errors and makes the demo instant.
const weatherCache = new Map();

// --- 2. HELPERS ---
const mean = (arr) => arr && arr.length > 0 ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
const sum = (arr) => arr && arr.length > 0 ? arr.reduce((a, b) => a + b, 0) : 0;

function getQueryDates(month) {
    const dates = [];
    const today = new Date();
    const currentYear = today.getFullYear();
    
    for (let i = 1; i <= 5; i++) {
        const year = currentYear - i;
        const startDate = `${year}-${String(month).padStart(2, '0')}-01`;
        const lastDay = new Date(year, month, 0).getDate();
        const endDate = `${year}-${String(month).padStart(2, '0')}-${lastDay}`;
        dates.push({ start_date: startDate, end_date: endDate });
    }
    return dates;
}

async function getEnvironmentalData(lat, lon, month = 7, irrigation = false) {
    // --- 1. CONFIGURATION ---
    const validLat = lat;
    const validLon = lon;

    // --- 3. CACHE CHECK ---
    const cacheKey = `${parseFloat(validLat).toFixed(2)}_${parseFloat(validLon).toFixed(2)}_${month}_${irrigation}`;
    
    if (weatherCache.has(cacheKey)) {
        const cached = weatherCache.get(cacheKey);
        const age = Date.now() - cached.timestamp;
        
        if (age < 600000) { 
            console.log(`⚡ [GeoAPI] Serving Cached Data for ${cacheKey} (Instant)`);
            return cached.data;
        }
    }

    console.log(`[GeoAPI] Fetching Fresh Weather for: ${validLat}, ${validLon} (Month: ${month}, Irrig: ${irrigation})...`);

    let result = {
        E_avg_temp: 0,
        E_max_temp: 0,
        E_total_rain_mm: 0,
        E_solar_radiation: 0,
        E_humidity_perc: 0,
        E_soil_moisture: 0,
        E_soil_ph: 7.0,
        E_soil_nitrogen: 0, 
        E_co2_ppm: 421.0, 
        E_o2_perc: 20.95
    };

    try {
        // --- 4. FETCH WEATHER ---
        const dates = getQueryDates(month);
        const weatherUrl = `https://archive-api.open-meteo.com/v1/archive`;
        
        const requests = dates.map(date => axios.get(weatherUrl, { 
            params: {
                latitude: validLat,
                longitude: validLon,
                start_date: date.start_date,
                end_date: date.end_date,
                daily: 'temperature_2m_max,temperature_2m_mean,rain_sum,shortwave_radiation_sum',
                hourly: 'relative_humidity_2m,soil_moisture_0_to_7cm'
            },
            timeout: 10000, 
            httpAgent, 
            httpsAgent
        }));

        const responses = await Promise.all(requests);

        // --- 5. AGGREGATE STATS ---
        let total_temp_mean = 0;
        let total_temp_max = 0;
        let total_rain_monthly = 0;
        let total_solar = 0;
        let total_humidity = 0;
        let total_soil_moisture = 0;

        responses.forEach(res => {
            const w = res.data;
            total_temp_mean += mean(w.daily.temperature_2m_mean);
            total_temp_max += Math.max(...w.daily.temperature_2m_max);
            total_rain_monthly += sum(w.daily.rain_sum);
            total_solar += mean(w.daily.shortwave_radiation_sum);
            total_humidity += mean(w.hourly.relative_humidity_2m);
            total_soil_moisture += mean(w.hourly.soil_moisture_0_to_7cm);
        });

        const count = responses.length;

        result.E_avg_temp = parseFloat((total_temp_mean / count).toFixed(2));
        result.E_max_temp = parseFloat((total_temp_max / count).toFixed(2));
        
        const avg_monthly_rain = total_rain_monthly / count;
        let final_rain_value = avg_monthly_rain * 12;

        // --- IRRIGATION LOGIC ---
        if (irrigation) {
            console.log("[GeoAPI] Irrigation ON: Overriding Rain with Optimal Water (1500mm)");
            final_rain_value = 1500;
        }

        result.E_total_rain_mm = parseFloat(final_rain_value.toFixed(2));
        
        result.E_solar_radiation = parseFloat((total_solar / count).toFixed(2));
        result.E_humidity_perc = parseFloat((total_humidity / count).toFixed(2));
        result.E_soil_moisture = parseFloat((total_soil_moisture / count).toFixed(2));

        // --- 6. CALCULATE SOIL PROXIES ---
        
        // A. pH Algorithm (Python will likely overwrite this with the 1.7GB file)
        // More Rain = More Acidic (Lower pH)
        let estimated_ph = 7.5 - (result.E_total_rain_mm / 2000);
        result.E_soil_ph = parseFloat(Math.min(Math.max(estimated_ph, 4.5), 8.5).toFixed(2));

        // B. Nitrogen Algorithm (Biogeochemical Proxy)
        // Replaces simple formula with Temperature + Moisture logic
        // Logic: Microbes need both Water and Heat (20-35°C) to make Nitrogen available.
        
        // Base Nitrogen from Moisture (Vegetation support)
        let n_base = 0.5 + (result.E_soil_moisture * 4.0);
        
        // Temperature Modifier
        let temp_factor = 1.0;
        if (result.E_avg_temp > 20 && result.E_avg_temp < 35) {
            temp_factor = 1.2; // Optimal decomposition heat
        }
        else {
            temp_factor = 0.8; // Too cold or too hot slows microbes
        }

        let estimated_n = n_base * temp_factor;
        
        // Clamp to realistic limits (0.5 to 4.0 g/kg)
        result.E_soil_nitrogen = parseFloat(Math.min(Math.max(estimated_n, 0.5), 4.0).toFixed(2));

        console.log(`[GeoAPI] Weather Ready. Calc pH: ${result.E_soil_ph}, Smart Calc N: ${result.E_soil_nitrogen}`);

        // --- 7. SAVE TO CACHE ---
        weatherCache.set(cacheKey, {
            timestamp: Date.now(),
            data: result
        });

    }
    catch (error) {
        console.error("[GeoAPI] Weather API Failed:", error.message);
    }

    return result;
}

module.exports = { getEnvironmentalData };