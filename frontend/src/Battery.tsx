import React from "react";
import "./Battery.css";

interface BatteryProps {
    charge: number;
}

const Battery: React.FC<BatteryProps> = ({ charge }) => {
    const maxBars = 10;
    const barWidth = 100;
    const barHeight = 32;
    const barSpacing = 5;
    const barStartY = 338;

    return (
        <svg width="100" height="480">
            {Array.from({ length: maxBars }).map((_, i) => {
                const threshold = (i * maxBars);
                if (charge <= threshold) return null;

                const y = barStartY - i * (barHeight + barSpacing);
                return(  
                    <rect 
                        x="24" y={y} 
                        width={barWidth} 
                        height={barHeight} 
                        fill="#BF5700"/>
                );
            })}
            <rect
                x="24" 
                y="375"
                width="100"
                height="99"
                fill="#333F48"
            />
            <text
                x="76"
                y="430"
                textAnchor="middle"
                alignmentBaseline="middle"
                fontSize="48"
                fill="white"
                fontWeight="bold"
            >
                {charge}
            </text>
        </svg>
    )
}

// const Battery: React.FC<BatteryProps> = ({ charge }) => {
//     const maxBars = 5;
//     const barWidth = 20;
//     const barSpacing = 5;
//     const barStartX = 50;
//     const barSkew = 10; // Skew to make parallelograms

//     return (
//         <svg width="200" height="100" viewBox="0 0 200 100">
//             {/* Background */}
//             <rect width="200" height="100" fill="black" />

//             {/* Battery shape */}
//             {/* <polyline
//                 points="30,30 60, 60 160, 60"
//                 stroke="white"
//                 strokeWidth="8"
//                 fill="none"
//             /> */}

//             {/* Parallelogram Bars (charge level) */}
//             <polygon 
//                 points="5,30 20,30 55,65 40,65" 
//                 fill="#BF5700"
//             />
//             {Array.from({ length: maxBars }).map((_, i) => {
//                 const threshold = ((i + 1) / maxBars) * 100;
//                 if (charge < threshold) return null;

//                 const x = barStartX + i * (barWidth + barSpacing);
//                 return (
//                     <polygon
//                     key={i}
//                     points={`
//                         ${x},55
//                         ${x + barWidth},55 
//                         ${x + barWidth + barSkew},65 
//                         ${x + barSkew},65
//                     `}
//                     fill="#BF5700"
//                     />
//                 );
//             })}

//             {/* Percentage text */}
//             <text
//                 x="100"
//                 y="40"
//                 fontSize="30"
//                 fill="white"
//                 textAnchor="middle"
//                 fontWeight="bold"
//             >
//                 {charge}%
//             </text>
//         </svg>
//     )
// };

export default Battery;