import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.xssf.usermodel.XSSFSheet;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

import java.io.File;
import java.io.FileInputStream;
import java.util.HashMap;
import java.util.Iterator;

/**
 * This class is to calculate energy consumption in kWH with the given input:
 * 1) average velocity,
 * 2) trip length,
 * 3) and average slope of road
 *
 * Created by Sangjae Bae on 1/11/17.
 */
public class Executable {
    private static HashMap<String, Double> hmEvParams;

    public static void main(String args[]){

        // <TEST> Input data - trip length, avg velocity, avg grade
        double linkLength = 11990d;
        double linkAvgVelocity = 8.75;
        double linkAvgGrade = 0d;
        HashMap<String, Double> inputArgs = new HashMap<>();
        inputArgs.put("linkLength",linkLength);
        inputArgs.put("linkAvgVelocity",linkAvgVelocity);
        inputArgs.put("linkAvgGrade",linkAvgGrade);

        // Load EV params
        initModel("Model X");

        // get energy consumption
        double linkEnergyKwh = getEnergyConsumption(inputArgs);
    }

    /**
     * Initialize consumption model
     */
    private static void initModel(String evModel) {
        // Load EV params
        String fPath ="/Users/mygreencar/Google Drive/beam-developers/model-inputs/vehicles/electric-vehicle-params.xlsx";
        hmEvParams = loadEvParams(fPath, evModel);
        System.out.println(hmEvParams.toString());
    }

    /**
     * Get energy consumption
     */
    public static double getEnergyConsumption(HashMap<String, Double> hmInputTrip) {
        // Initialize conversion/general params
        double coeff = 0.64;
        double mps2mph = 2.236936;
        double lbf2N = 4.448222;
        double lbs2kg = 0.453592;
        double gravity = 9.8;

        // Calculate average power of the itinerary
        double linkAvgVelocityMph = hmInputTrip.get("linkAvgVelocity") * mps2mph;
        double massKg = hmEvParams.get("mass") * lbs2kg;
        double powerAvgKw = ((hmEvParams.get("coefA")
                + hmEvParams.get("coefB")*linkAvgVelocityMph
                + hmEvParams.get("coefC")*Math.pow(linkAvgVelocityMph,2))*lbf2N
                + massKg * gravity * Math.sin(hmInputTrip.get("linkAvgGrade")))*hmInputTrip.get("linkAvgVelocity")/1000;
        System.out.println("Average power (kW): " + powerAvgKw +"\n");

        // Calculate average energy consumption with the average power
        double periodS = hmInputTrip.get("linkLength")/hmInputTrip.get("linkAvgVelocity");
        double linkEnergyKwhIdeal = powerAvgKw * periodS / 3600;
        double linkEnergyKwh = linkEnergyKwhIdeal/coeff;
        System.out.println("Energy consumption (kWh): " + linkEnergyKwh + "\n");

        return linkEnergyKwh;
    }

    /**
     * Load params used to calculate Energy consumptions of EV models
     */
    private static HashMap<String,Double> loadEvParams(String fPath, String evModel) {
        HashMap<String,Double> hmEvParams = new HashMap<>();

        try{
            FileInputStream file = new FileInputStream(new File(fPath));

            // Create Workbook instance holding reference to .xlsx file
            XSSFWorkbook workbook = new XSSFWorkbook(file);

            // Get first/desired sheet from the workbook
            XSSFSheet sheet = workbook.getSheetAt(0);

            // Get the row number for the given ev Model;
            // - select Nissan leaf if no EV model is given
            // - select Nissan leaf if the given EV model does not exist in the ev data sheet
            int rowNumForEv = sheet.getLastRowNum();
            if(evModel != null){ // if EV model is given
                for(int i = 1; i<sheet.getLastRowNum();i++){
                    if(sheet.getRow(i).getCell(1).getStringCellValue().contains(evModel)){
                        rowNumForEv = i;
                        break;
                    }
                }
            }
            System.out.println("Row num for EV: " + rowNumForEv);
            System.out.println("Selected EV model: " + sheet.getRow(rowNumForEv).getCell(1).getStringCellValue());

            // Parse params from the sheet
            double mass = Double.valueOf(sheet.getRow(rowNumForEv).getCell(4).getRawValue());
            double coefA = Double.valueOf(sheet.getRow(rowNumForEv).getCell(5).getRawValue());
            double coefB = Double.valueOf(sheet.getRow(rowNumForEv).getCell(6).getRawValue());
            double coefC = Double.valueOf(sheet.getRow(rowNumForEv).getCell(7).getRawValue());

            // Put params in hashMap
            hmEvParams.put("mass",mass);
            hmEvParams.put("coefA",coefA);
            hmEvParams.put("coefB",coefB);
            hmEvParams.put("coefC",coefC);

            // Do not forget to close the file after use
            file.close();
        }catch (Exception e){
            e.printStackTrace();
        }

        // Return the EV parameters; it returns an empty HashMap if the input file does not exist or inaccessible. A crash will occur.
        return hmEvParams;
    }
}
