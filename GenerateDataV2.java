package com.company;

import com.opencsv.CSVReader;

import java.io.FileReader;
import java.io.FileWriter;
import java.util.ArrayList;

public class GenerateDataV2 {
    public static void generateData(String pair, int vision, double stop, double profit) throws Exception {

        System.out.println("src/main/resources/"+pair+"/history.csv");
        // Reading and Writing
        CSVReader csvReader1m = new CSVReader(new FileReader("src/main/resources/"+pair+"/1mhistory.csv"));
        CSVReader csvReader1h = new CSVReader(new FileReader("src/main/resources/"+pair+"/1hhistory.csv"));
        FileWriter writer = new FileWriter("src/main/resources/"+pair+"/training.csv");

        // Write column names
        for(int i = 0; i< 800; i++){
            writer.write(i + ",");
        }
        writer.write("Position\n");


        // Set up buffers
        ArrayList<String[]> csvBuffer1m = new ArrayList<String[]>();
        ArrayList<String[]> csvBuffer1h = new ArrayList<String[]>();
        String Linebuffer = "";

        //Skip the first line with column names
        csvReader1m.readNext();
        csvReader1h.readNext();

        // Buffer up first 49+vision lines for 1m candles
        for(int i = 0; i < 49+vision; i++){
            csvBuffer1m.add(csvReader1m.readNext());
        }

        // Buffer up the first 50 1h candles
        for(int i = 0; i< 50; i++){
            csvBuffer1h.add(csvReader1h.readNext());
        }

        //Slide the buffer up right until the first 1m candle to be processed
        double timestamp = Double.parseDouble(csvBuffer1m.get(49)[0]);
        while(Double.parseDouble(csvReader1h.peek()[0]) <= timestamp){
            // Add to buffer
            csvBuffer1h.add(csvReader1h.readNext());
            // Remove oldest
            csvBuffer1h.remove(0);
        }


        // Storing csv row which is being read one line at a time
        String[] row = null;

        // Convenient counters
        int count = 0; // How many rows we processed
        int positioncount = 0; // How many positions were taken

        // Main loop
        System.out.println("Starting main loop");
        while((row = csvReader1m.readNext())!= null){
            // Print counter
            count++;
            System.out.println(count);

            // Add latest to buffer
            csvBuffer1m.add(row);

            // Squash each relevant line in the buffer
            for(int i = 0; i < 50; i++){
                Linebuffer += preprocess(csvBuffer1m.get(i) ,csvBuffer1m.get(49));
            }
            // Get rid of the first comma in the line buffer from preprocessing
            Linebuffer = Linebuffer.substring(1);

            // DETERMINE WHETHER TO MOVE THE 1H BUFFER UP
            if((csvReader1h.peek()!=null) && Double.parseDouble(csvReader1h.peek()[0])<= Double.parseDouble(csvBuffer1m.get(49)[0])){
                // Add to buffer
                csvBuffer1h.add(csvReader1h.readNext());
                // Remove oldest
                csvBuffer1h.remove(0);
            }

            // Getting the last 50 candles for the 1h timeframe and add to the linebuffer
            for(int i = 0; i < 50; i++){
                Linebuffer += preprocess(csvBuffer1h.get(i) ,csvBuffer1h.get(49));
            }


            // DETERMINING WHICH POSITION TO TAKE
            // Position to take, 0 for neutral, 1 for short, 2 for long
            int position = 0;

            // Closing price of time which we are trying to take a position at
            double price  = Double.parseDouble(csvBuffer1m.get(49)[4]);

            // Allocating variables
            double low = 0;
            double high = 0;

            // Check for longs
            for( int i = 50; i < 50+vision; i++){
                // Get high/low for this row
                low = Double.parseDouble(csvBuffer1m.get(i)[3]);
                high = Double.parseDouble(csvBuffer1m.get(i)[3]);

                //check if stopped out
                if((1- price/low) <= -stop){
                    break;
                }
                if((1- price/high) >= profit){
                    position = 2;
                    positioncount++;
                    break;
                }
            }
            // Check for shorts
            for( int i = 50; i < 50+vision; i++){
                // Get high/low for this row
                low = Double.parseDouble(csvBuffer1m.get(i)[3]);
                high = Double.parseDouble(csvBuffer1m.get(i)[3]);

                //check if stopped out
                if((1- price/high) >= stop){
                    break;
                }
                if((1- price/low) <= -profit){
                    position = 1;
                    positioncount++;
                    break;
                }
            }

            // Write out line, clear buffer
            writer.write(Linebuffer + ", "+ position +"\n");
            Linebuffer = "";

            // Remove the oldest row
            csvBuffer1m.remove(0);
        }
        // Print results
        System.out.println("Training data complete, "+ positioncount +" valid positions out of "+ count +" ("+(positioncount/count)+"%)");

        // Close writer
        writer.close();
    }

    public static String preprocess(String[] data, String[] newest){
        //Normalize values for neural network
        String buffer = "";
        //time open high low close volume fastk slowk adx
        // normalize prices
        for (int i = 1; i < 5; i++){
            buffer += ","+ (1 - (Double.parseDouble(data[i]))/(Double.parseDouble(newest[i])))*10;
        }
        //Volume
        if((Double.parseDouble(data[5])== 0)|| (Double.parseDouble(newest[5])== 0)){
            buffer += ",0";

        }else{
            buffer += ","+ (1 - (Double.parseDouble(data[5])/Double.parseDouble(newest[5])))/10;
        }

        //ADX and stochastic
        for (int i = 6; i < 9; i++){
            buffer += "," + (Double.parseDouble(data[i])-50)/100;
        }

        if(buffer.contains("Infinity")){
            System.out.println(newest[0]);
        }
        return buffer;
    }
}
