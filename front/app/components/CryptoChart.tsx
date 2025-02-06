"use client"
import React, { useState, useEffect, useRef } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from 'chart.js';
import { useTime } from '../context/CryptoContext';

// Enregistrer les composants nécessaires de Chart.js
ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

const CryptoChart = () => {
  const MAX_DATA_POINTS = 10; // Nombre maximum de points de données affichés
  const { time } = useTime();   // Utiliser `time` depuis le contexte
  const step = 3; // Intervalle de 3 heures entre chaque point

  // Fonction pour générer un label d'heure en fonction de l'heure précédente
  const generateTimeLabel = (previousLabel: string) => {
    // Extraire l'heure et la minute à partir de l'ancien label
    const [hours, minutes] = previousLabel.split("h").map(Number);
    
    // Ajouter l'intervalle de temps (step) aux heures
    const newHour = (hours + step) % 24;  // Remet à 0 après 24 heures
    
    // Formater la nouvelle heure en 'HHhMM'
    return `${newHour.toString().padStart(2, '0')}h00`;
  };

  // État pour les données du graphique
  const [chartData, setChartData] = useState({
    labels: ["00h00", "03h00", "06h00", "09h00", "12h00", "15h00"], // Labels initiaux pour le temps (en heures)
    datasets: [
      {
        label: 'Prix du Bitcoin',
        data: [4500, 4700, 4600, 4800, 4550, 4700], // Prix initiaux pour correspondre aux labels
        borderColor: 'rgba(75, 192, 192, 1)',
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        fill: true,
        tension: 0.4,
      },
    ],
  });

  const chartRef = useRef(null);

  // Fonction pour simuler l'arrivée d'une nouvelle valeur (par exemple via API)
  const fetchNewData = () => {
    const newPrice = Math.floor(1000 + Math.random() * 5000); // Générer un prix entre 1000 et 6000
    const lastLabel = chartData.labels[chartData.labels.length - 1]; // Obtenir le dernier label
    const timeLabel = generateTimeLabel(lastLabel); // Générer le nouveau label basé sur le dernier
    let chartdataTemp = chartData;
    chartdataTemp.labels.push(timeLabel)
    chartData.datasets[0].data.push(newPrice)
    
  
      // Si le nombre de labels dépasse le maximum, supprimer les plus anciens
      if (chartdataTemp.labels.length > MAX_DATA_POINTS) {
        chartdataTemp.labels.shift();
        chartdataTemp.datasets[0].data.shift();
      }
      
      setChartData(chartData)
  };

  // Effet pour mettre à jour les données toutes les `time` secondes
  useEffect(() => {
    const interval = setInterval(() => {
      fetchNewData();
      if (chartRef.current) {
        (chartRef.current as any).update(); // Mettre à jour le graphique
      }
    }, time * 1000);

    return () => clearInterval(interval); // Nettoyage de l'intervalle
  }, [time]);

  // Mise à jour des options avec les limites des labels y entre 1000 et 6000
  const options = {
    responsive: true,
    animation: {
      duration: 500,
    },
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Historique des prix du Bitcoin (24 heures)',
      },
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Temps (HH:mm)',
        },
      },
      y: {
        title: {
          display: true,
          text: 'Prix en USD',
        },
        beginAtZero: false,
        min: 1000,  // Minimum des labels y
        max: 6000,  // Maximum des labels y
      },
    },
  };

  return (
    <div>
      <Line ref={chartRef} data={chartData} options={options} />
    </div>
  );
};

export default CryptoChart;
