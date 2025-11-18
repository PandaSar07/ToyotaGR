from flask import Flask, request, jsonify
import pandas as pd
import os

app = Flask(__name__)

# --- STEP 1: Load and Combine All CSVs ---
def load_dataset():
    folder_path = 'data/'
    csv_files = [f for f in os.listdir(folder_path) if f.endswith('.csv')]

    if not csv_files:
        raise FileNotFoundError("No CSV files found in the data folder.")

    df_list = []
    for file in csv_files:
        try:
            # Use semicolon separator
            data = pd.read_csv(os.path.join(folder_path, file), sep=';')
            data['source_file'] = file  # Keep track of which race it came from
            df_list.append(data)
        except Exception as e:
            print(f"⚠️ Could not read {file}: {e}")

    df = pd.concat(df_list, ignore_index=True)
    print(f"✅ Loaded {len(csv_files)} CSV files, total rows: {len(df)}")
    df.columns = df.columns.str.upper().str.strip()
    return df

df = load_dataset()

# --- STEP 2: API Route ---
@app.route('/analyze', methods=['POST'])
def analyze_driver():
    data = request.get_json()
    driver_name = data.get('driver')
    race_name = data.get('race')

    if not driver_name or not race_name:
        return jsonify({'error': 'Please provide both driver and race.'}), 400

    # Filter by driver and race (race_name = CSV file name)
    subset = df[
        (df['SOURCE_FILE'].str.lower() == race_name.lower()) &
        (df['DRIVER_*EXTRA 3'].str.lower().str.contains(driver_name.lower(), na=False))
    ]

    if subset.empty:
        return jsonify({'error': 'No data found for that driver or race.'}), 404

    # --- STEP 3: Analytics ---
    position = subset['POSITION'].iloc[0] if 'POSITION' in subset else None
    laps = subset['LAPS'].mean() if 'LAPS' in subset else None
    total_time = subset['TOTAL_TIME'].iloc[0] if 'TOTAL_TIME' in subset else None
    fast_lap_time = subset['FL_TIME'].iloc[0] if 'FL_TIME' in subset else None
    fast_lap_kph = subset['FL_KPH'].iloc[0] if 'FL_KPH' in subset else None
    vehicle = subset['VEHICLE'].iloc[0] if 'VEHICLE' in subset else None
    tires = subset['TIRES'].iloc[0] if 'TIRES' in subset else None

    analytics = {
        'driver': driver_name,
        'race_file': race_name,
        'position': position,
        'laps_completed': int(laps) if pd.notna(laps) else None,
        'total_time': total_time,
        'fastest_lap_time': fast_lap_time,
        'fastest_lap_speed_kph': fast_lap_kph,
        'vehicle': vehicle,
        'tires': tires
    }

    return jsonify(analytics)

# --- STEP 4: Run ---
if __name__ == '__main__':
    app.run(debug=True)
