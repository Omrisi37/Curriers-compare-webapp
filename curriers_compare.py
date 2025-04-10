import pandas as pd
import streamlit as st

def main():
    st.title("Shipping Price Comparison Tool")
    
    # Hardcoded file paths
    dhl_mapping_path = "dhl pricing.xlsx"
    fedex_mapping_path = "fedex pricing.xlsx"
    pricing_table_path = "pricing table.xlsx"
    
    try:
        # Load all data files
        dhl_mapping_df = pd.read_excel(dhl_mapping_path)
        fedex_mapping_df = pd.read_excel(fedex_mapping_path)
        pricing_table_df = pd.read_excel(pricing_table_path)
        
        # Display success messages
        st.sidebar.success("All data files loaded successfully")
        
        # Get list of unique countries from DHL mapping
        countries = sorted(dhl_mapping_df.iloc[:, 0].unique())
        
        # User inputs
        selected_country = st.selectbox("Select Country", countries)
        weight = st.number_input("Enter Weight (kg)", min_value=0.1, value=5.0, step=0.1)
        
        if st.button("Compare Prices"):
            # Extract country name without code for FedEx lookup
            if "(" in selected_country and ")" in selected_country:
                # For countries like "Cayman Islands (KY)"
                country_without_code = selected_country.split(" (")[0].strip()
            else:
                country_without_code = selected_country
            
            # Find area codes
            dhl_row = dhl_mapping_df[dhl_mapping_df.iloc[:, 0] == selected_country]
            fedex_row = fedex_mapping_df[fedex_mapping_df.iloc[:, 0] == country_without_code]
            
            if not dhl_row.empty and not fedex_row.empty:
                # Extract area numbers
                dhl_area = int(dhl_row.iloc[0, 1])
                fedex_area = int(fedex_row.iloc[0, 1])
                
                # Construct column names for pricing table lookup
                dhl_col = f"AREA{dhl_area} DHL"
                fedex_col = f"AREA{fedex_area} FEDEX"
                
                try:
                    # Filter out non-numeric rows from pricing table
                    numeric_rows = []
                    for i, row in pricing_table_df.iterrows():
                        try:
                            kg_val = row.iloc[0]
                            if isinstance(kg_val, (int, float)) or (isinstance(kg_val, str) and kg_val.replace('.', '', 1).isdigit()):
                                numeric_rows.append(i)
                        except:
                            pass
                    
                    filtered_pricing_df = pricing_table_df.iloc[numeric_rows]
                    
                    # Determine if we need standard pricing or extra kg pricing
                    WEIGHT_THRESHOLD = 30  # Adjust based on your actual threshold
                    
                    # Calculate price based on weight tier
                    if weight <= WEIGHT_THRESHOLD:
                        # Standard pricing for weights up to threshold
                        weights_list = filtered_pricing_df.iloc[:, 0].tolist()
                        try:
                            weights_list = [float(w) for w in weights_list if w <= WEIGHT_THRESHOLD]
                            closest_weight = min(weights_list, key=lambda x: abs(float(x) - weight))
                            weight_row = filtered_pricing_df[filtered_pricing_df.iloc[:, 0] == closest_weight]
                            
                            if not weight_row.empty and dhl_col in weight_row.columns and fedex_col in weight_row.columns:
                                dhl_price = float(weight_row[dhl_col].values[0])
                                fedex_price = float(weight_row[fedex_col].values[0])
                                price_type = "Standard price"
                            else:
                                st.error(f"Price not found for weight {closest_weight}kg")
                                return
                        except:
                            st.error("Error processing standard pricing")
                            return
                    else:
                        # Extra kg pricing for weights above threshold
                        try:
                            # 1. Get base price for threshold weight
                            base_weight_row = filtered_pricing_df[filtered_pricing_df.iloc[:, 0] == WEIGHT_THRESHOLD]
                            if base_weight_row.empty:
                                # Find closest weight to threshold
                                weights_list = [float(w) for w in filtered_pricing_df.iloc[:, 0].tolist() if w <= WEIGHT_THRESHOLD]
                                closest_threshold = max(weights_list)
                                base_weight_row = filtered_pricing_df[filtered_pricing_df.iloc[:, 0] == closest_threshold]
                            
                            dhl_base_price = float(base_weight_row[dhl_col].values[0])
                            fedex_base_price = float(base_weight_row[fedex_col].values[0])
                            
                            # 2. Find the extra kg price 
                            # Find the row with "PRICE FOR 1KG EXTRA 31-70KG" or similar
                            extra_price_row = None
                            for i, row in pricing_table_df.iterrows():
                                if isinstance(row.iloc[0], str) and "EXTRA" in row.iloc[0]:
                                    # Find the first numeric row after this header
                                    for j in range(i+1, len(pricing_table_df)):
                                        try:
                                            # Use the first row after the header as the per-kg price
                                            extra_price_row = pricing_table_df.iloc[j]
                                            # Test if we can access the price columns
                                            float(extra_price_row[dhl_col])
                                            float(extra_price_row[fedex_col])
                                            break
                                        except:
                                            continue
                                    break
                            
                            if extra_price_row is not None:
                                # Calculate price: base price + (extra kg × price per extra kg)
                                extra_kg = weight - WEIGHT_THRESHOLD
                                dhl_extra_price = float(extra_price_row[dhl_col])
                                fedex_extra_price = float(extra_price_row[fedex_col])
                                
                                dhl_price = dhl_base_price + (extra_kg * dhl_extra_price)
                                fedex_price = fedex_base_price + (extra_kg * fedex_extra_price)
                                price_type = f"Base price for {WEIGHT_THRESHOLD}kg + {extra_kg:.1f}kg extra"
                            else:
                                st.error("Could not find extra kg pricing")
                                return
                        except Exception as e:
                            st.error(f"Error processing extra kg pricing: {e}")
                            return
                    
                    # Display results
                    st.subheader("Comparison Results")
                    
                    comparison_data = {
                        "Courier": ["DHL", "FEDEX"],
                        "Area": [dhl_area, fedex_area],
                        "Price ($)": [dhl_price, fedex_price]
                    }
                    
                    comparison_df = pd.DataFrame(comparison_data)
                    st.write(f"Shipping from {selected_country}")
                    st.write(f"Weight: {weight}kg ({price_type})")
                    st.dataframe(comparison_df)
                    
                    # Highlight cheaper courier
                    cheaper_courier = "DHL" if dhl_price < fedex_price else "FEDEX"
                    price_diff = abs(dhl_price - fedex_price)
                    savings_percent = (price_diff / max(dhl_price, fedex_price)) * 100
                    
                    st.success(f"**{cheaper_courier}** is cheaper by **${price_diff:.2f}** ({savings_percent:.1f}%)")
                
                except Exception as e:
                    st.error(f"Error calculating prices: {e}")
            else:
                st.error(f"Area codes not found for country: {selected_country}")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
