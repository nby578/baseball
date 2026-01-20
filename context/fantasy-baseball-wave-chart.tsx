import React, { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const FantasyBaseballWaveChart = () => {
  const teams = {
    "Kershawshank Raydemption": {
      weeks: { 
        1: 703.9, 2: 716.87, 3: 764.87, 4: 636.27, 5: 680.80, 6: 755.47, 7: 561.73, 8: 737.33, 9: 726.70, 10: 821.60, 11: 724.10, 12: 734.20, 13: 623.30, 14: 855.57, 15: 675.2, 16: 794.00, 17: 645.73, 18: 651.07, 19: 566.43, 20: 440.53, 21: 696.10, 22: null
      },
      record: "15-5-0", finalRank: 3, color: "#FF6B6B", madePlayoffs: true
    },
    "A Pair O' Perez": {
      weeks: { 
        1: 654.5, 2: 732.23, 3: 870.30, 4: 878.77, 5: 555.13, 6: 622.47, 7: 681.47, 8: 890.60, 9: 731.10, 10: 866.20, 11: 697.83, 12: 801.63, 13: 831.53, 14: 617.17, 15: 910.9, 16: 953.20, 17: 781.80, 18: 713.37, 19: 599.70, 20: 805.40, 21: 803.73, 22: null
      },
      record: "16-4-0", finalRank: 1, color: "#4ECDC4", madePlayoffs: true
    },
    "Sasaki Bohms": {
      weeks: { 
        1: 649.9, 2: 655.00, 3: 830.50, 4: 609.53, 5: 700.97, 6: 645.90, 7: 618.87, 8: 598.07, 9: 615.30, 10: 725.70, 11: 780.60, 12: 589.24, 13: 544.70, 14: 722.50, 15: 692.8, 16: 462.63, 17: 748.20, 18: 610.20, 19: 608.03, 20: 570.50, 21: null
      },
      record: "12-8-0", finalRank: 5, color: "#45B7D1", madePlayoffs: true, eliminated: 21
    },
    "Bach & Veovaldi": {
      weeks: { 
        1: 533.8, 2: 754.50, 3: 594.50, 4: 653.90, 5: 587.13, 6: 833.03, 7: 753.00, 8: 847.67, 9: 555.73, 10: 562.90, 11: 595.67, 12: 711.70, 13: 815.80, 14: 597.17, 15: 544.5, 16: 575.57, 17: 779.13, 18: 726.00, 19: 771.73, 20: 582.07, 21: 885.63, 22: null
      },
      record: "13-7-0", finalRank: 4, color: "#74B9FF", madePlayoffs: true
    },
    "A-A-Ron": {
      weeks: { 
        1: 739.3, 2: 739.67, 3: 710.13, 4: 676.70, 5: 837.27, 6: 750.20, 7: 805.67, 8: 740.37, 9: 680.40, 10: 759.33, 11: 885.67, 12: 879.63, 13: 592.57, 14: 799.17, 15: 844.3, 16: 552.93, 17: 740.10, 18: 627.13, 19: 1042.17, 20: 729.97, 21: 787.00, 22: null
      },
      record: "16-4-0", finalRank: 2, color: "#00B894", madePlayoffs: true
    },
    "Melech ha Baseball": {
      weeks: { 
        1: 496.9, 2: 576.80, 3: 406.83, 4: 577.80, 5: 820.10, 6: 590.47, 7: 791.77, 8: 655.40, 9: 665.03, 10: 683.70, 11: 584.70, 12: 842.07, 13: 604.00, 14: 663.37, 15: 754.2, 16: 546.90, 17: 596.20, 18: 666.20, 19: 577.73, 20: 732.83, 21: null
      },
      record: "11-9-0", finalRank: 6, color: "#FD79A8", madePlayoffs: true, eliminated: 21
    }
  };

  const [selectedTeams, setSelectedTeams] = useState(Object.keys(teams));

  const chartData = useMemo(() => {
    const weeks = Array.from({length: 22}, (_, i) => i + 1);
    return weeks.map(week => {
      const weekData = { week };
      selectedTeams.forEach(teamName => {
        if (teams[teamName] && teams[teamName].weeks[week] !== null && teams[teamName].weeks[week] !== undefined) {
          weekData[teamName] = teams[teamName].weeks[week];
        }
      });
      return weekData;
    });
  }, [selectedTeams]);

  const yAxisBounds = useMemo(() => {
    if (selectedTeams.length === 0) return { min: 400, max: 1000 };
    
    let allScores = [];
    selectedTeams.forEach(teamName => {
      if (teams[teamName]) {
        const validScores = Object.values(teams[teamName].weeks).filter(score => score !== null && score !== undefined);
        allScores = allScores.concat(validScores);
      }
    });
    
    if (allScores.length === 0) return { min: 400, max: 1000 };
    
    const minScore = Math.min(...allScores);
    const maxScore = Math.max(...allScores);
    const padding = (maxScore - minScore) * 0.1;
    
    return {
      min: Math.max(0, Math.floor((minScore - padding) / 50) * 50),
      max: Math.ceil((maxScore + padding) / 50) * 50
    };
  }, [selectedTeams]);

  const handleTeamToggle = (teamName) => {
    setSelectedTeams(prev => 
      prev.includes(teamName) 
        ? prev.filter(t => t !== teamName)
        : [...prev, teamName]
    );
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Fantasy Baseball 2025 - Season Wave Chart</h1>
      
      {/* Playoff Status */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Current Playoff Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="font-semibold text-green-800 mb-2">Week 22 Semifinals</h3>
            <div className="space-y-2">
              <div className="text-green-700">A-A-Ron vs Kershawshank Raydemption</div>
              <div className="text-green-700">A Pair O' Perez vs Bach & Veovaldi</div>
            </div>
          </div>
          <div className="bg-red-50 p-4 rounded-lg">
            <h3 className="font-semibold text-red-800 mb-2">Eliminated in Week 21</h3>
            <div className="space-y-1">
              <div className="text-red-700">Sasaki Bohms</div>
              <div className="text-red-700">Melech ha Baseball</div>
            </div>
          </div>
        </div>
      </div>
      
      {/* Team Selection */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Select Teams to Display</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {Object.keys(teams).map(teamName => {
            const team = teams[teamName];
            const isEliminated = team.eliminated;
            return (
              <label key={teamName} className="flex items-center space-x-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedTeams.includes(teamName)}
                  onChange={() => handleTeamToggle(teamName)}
                  className="w-4 h-4 text-blue-600"
                />
                <span className={`text-sm truncate ${isEliminated ? 'text-gray-500 line-through' : 'text-gray-700'}`}>
                  {teamName} (#{team.finalRank}) 
                  {isEliminated && ' - Eliminated Week 21'}
                </span>
              </label>
            );
          })}
        </div>
        <div className="mt-4 flex gap-2">
          <button
            onClick={() => setSelectedTeams(Object.keys(teams))}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Select All
          </button>
          <button
            onClick={() => setSelectedTeams([])}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Clear All
          </button>
          <button
            onClick={() => setSelectedTeams(Object.keys(teams).filter(name => !teams[name].eliminated))}
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Show Remaining Teams
          </button>
        </div>
      </div>

      {/* Wave Chart */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Season Performance Wave</h2>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="week" 
                domain={[1, 22]}
                type="number"
                ticks={[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]}
              />
              <YAxis domain={[yAxisBounds.min, yAxisBounds.max]} />
              <Tooltip 
                formatter={(value, name) => [Math.round(value), name]}
                labelFormatter={(label) => {
                  if (label <= 20) return `Week ${label}`;
                  if (label === 21) return `Week 21 (Quarterfinals)`;
                  if (label === 22) return `Week 22 (Semifinals)`;
                  return `Week ${label}`;
                }}
              />
              <Legend />
              {selectedTeams.map(teamName => {
                const team = teams[teamName];
                const isEliminated = team.eliminated;
                return (
                  <Line
                    key={teamName}
                    type="monotone"
                    dataKey={teamName}
                    stroke={team.color}
                    strokeWidth={isEliminated ? 1 : 3}
                    strokeDasharray={isEliminated ? "5,5" : "0"}
                    dot={{ r: isEliminated ? 2 : 4 }}
                    connectNulls={false}
                  />
                );
              })}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Chart Legend</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-1 bg-gray-600"></div>
            <span className="text-sm">Active Team (Thick Line)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-1 bg-gray-400 opacity-50" style={{borderTop: '1px dashed #666'}}></div>
            <span className="text-sm">Eliminated Team (Dashed Line)</span>
          </div>
          <div className="text-sm text-gray-600">
            <div><strong>Weeks 1-20:</strong> Regular Season</div>
            <div><strong>Week 21:</strong> Quarterfinals</div>
            <div><strong>Week 22:</strong> Semifinals (Pending)</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FantasyBaseballWaveChart;