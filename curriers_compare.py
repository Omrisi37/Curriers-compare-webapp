import pandas as pd
import streamlit as st

def main():
    st.title("Shipping Price Comparison Tool")
    
    # Hardcoded file paths
    dhl_mapping_path = "data/dhl_mapping.xlsx"
    fedex_mapping_path = "data/fedex_mapping.xlsx"
    pricing_table_path = "data/pricing_table.xlsx"
    
    try:
        # Load all data files
        dhl_mapping_df = pd.read_excel(dhl_mapping_path)
        fedex_mapping_df = pd.read_excel(fedex_mapping_path)
        pricing_table_df = pd.read_excel(pricing_table_path)
        
        st.sidebar.success("DHL mapping data loaded successfully")
        st.sidebar.success("FedEx mapping data loaded successfully")
        st.sidebar.success("Pricing table data loaded successfully")
        
        # Get countries list from DHL mapping (using first column)
        # Assuming your mapping has country names in first column and area numbers in second column
        countries = sorted(list(set(dhl_mapping_df.iloc[:, 0].dropna().tolist())))
        
        # User inputs
        country_name = st.selectbox("Select Country", countries)
        weight = st.number_input("Enter Weight (kg)", min_value=0.1, value=15.0, step=0.1)
        
        if st.button("Compare Prices"):
            # Find the area for each courier
            dhl_row = dhl_mapping_df[dhl_mapping_df.iloc[:, 0] == country_name]
            fedex_row = fedex_mapping_df[fedex_mapping_df.iloc[:, 0] == country_name]
            
            if not dhl_row.empty and not fedex_row.empty:
                # Get area numbers (1-6) from the second column of mapping files
                dhl_area = int(dhl_row.iloc[0, 1])
                fedex_area = int(fedex_row.iloc[0, 1])
                
                # Find closest weight in pricing table
                weights = pricing_table_df.iloc[:, 0].tolist()
                closest_weight = min(weights, key=lambda x: abs(float(x) - weight))
                weight_row = pricing_table_df[pricing_table_df.iloc[:, 0] == closest_weight]
                
                if not weight_row.empty:
                    # Construct column names based on area numbers
                    dhl_col = f"AREA{dhl_area} DHL"
                    fedex_col = f"AREA{fedex_area} FEDEX"
                    
                    # Get prices from pricing table
                    if dhl_col in pricing_table_df.columns and fedex_col in pricing_table_df.columns:
                        dhl_price = float(weight_row[dhl_col].values[0])
                        fedex_price = float(weight_row[fedex_col].values[0])
                        
                        # Display results
                        st.subheader("Comparison Results")
                        
                        # Create comparison dataframe
                        comparison_df = pd.DataFrame({
                            "Courier": ["DHL", "FEDEX"],
                            "Area": [dhl_area, fedex_area],
                            "Price ($)": [dhl_price, fedex_price]
                        })
                        
                        st.write(f"Shipping from {country_name}")
                        st.write(f"Weight: {closest_weight}kg")
                        st.dataframe(comparison_df)
                        
                        # Show which courier is cheaper
                        cheaper = "DHL" if dhl_price < fedex_price else "FEDEX"
                        price_diff = abs(dhl_price - fedex_price)
                        savings_pct = (price_diff / max(dhl_price, fedex_price)) * 100
                        
                        st.success(f"**{cheaper}** is cheaper by **${price_diff:.2f}** ({savings_pct:.1f}%)")
                        
                        # Add visualization
                        st.bar_chart(comparison_df.set_index("Courier")["Price ($)"])
                    else:
                        st.error(f"Column names not found. Looking for {dhl_col} and {fedex_col}")
                else:
                    st.error(f"Weight {weight}kg not found in pricing table")
            else:
                st.error(f"Area codes not found for country: {country_name}")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
