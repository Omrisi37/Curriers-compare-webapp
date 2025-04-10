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
        
        st.sidebar.success("DHL mapping data loaded successfully")
        st.sidebar.success("FedEx mapping data loaded successfully")
        st.sidebar.success("Pricing table data loaded successfully")
        
       # Clean the pricing table - keep only rows with numeric values in the KG column
        numeric_rows = []
        for i, row in pricing_table_df.iterrows():
            try:
                # Try to convert the value in the KG column to float
                float(row.iloc[0])
                numeric_rows.append(i)
            except (ValueError, TypeError):
                # Skip rows with non-numeric values
                continue
        
        pricing_table_df = pricing_table_df.iloc[numeric_rows]
        
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
                
                # Find closest weight in pricing table
                weights_list = pricing_table_df.iloc[:, 0].tolist()
                try:
                    weights_list = [float(w) for w in weights_list]
                    closest_weight = min(weights_list, key=lambda x: abs(float(x) - weight))
                    weight_row = pricing_table_df[pricing_table_df.iloc[:, 0] == closest_weight]
                    
                    if not weight_row.empty:
                        # Construct column names for pricing table lookup
                        dhl_col = f"AREA{dhl_area} DHL"
                        fedex_col = f"AREA{fedex_area} FEDEX"
                        
                        if dhl_col in pricing_table_df.columns and fedex_col in pricing_table_df.columns:
                            try:
                                # Get prices from pricing table
                                dhl_price = float(weight_row[dhl_col].values[0])
                                fedex_price = float(weight_row[fedex_col].values[0])
                                
                                # Display results
                                st.subheader("Comparison Results")
                                
                                comparison_data = {
                                    "Courier": ["DHL", "FEDEX"],
                                    "Area": [dhl_area, fedex_area],
                                    "Price ($)": [dhl_price, fedex_price]
                                }
                                
                                comparison_df = pd.DataFrame(comparison_data)
                                st.write(f"Shipping from {selected_country}")
                                st.write(f"Weight: {closest_weight}kg")
                                st.dataframe(comparison_df)
                                
                                # Highlight cheaper courier
                                cheaper_courier = "DHL" if dhl_price < fedex_price else "FEDEX"
                                price_diff = abs(dhl_price - fedex_price)
                                savings_percent = (price_diff / max(dhl_price, fedex_price)) * 100
                                
                                st.success(f"**{cheaper_courier}** is cheaper by **${price_diff:.2f}** ({savings_percent:.1f}%)")
                            except (ValueError, TypeError):
                                st.error(f"Non-numeric price values found. Please check the pricing table.")
                        else:
                            st.error(f"Price columns not found: {dhl_col} or {fedex_col}")
                            st.write("Available columns:", pricing_table_df.columns.tolist())
                    else:
                        st.error(f"Weight {weight}kg not found in pricing table.")
                except (ValueError, TypeError):
                    st.error("Issue with weight values in the pricing table.")
            else:
                st.error(f"Area codes not found for country: {selected_country}.")
                # Don't show the first 10 countries
    
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
