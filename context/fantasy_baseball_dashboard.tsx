import React, { useState, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const FantasyFootballDashboard = () => {
  const teams = {
    "Kirby's DreamYand": {
      weeks: {
        1: 614.1, 2: 728.77, 3: 766.73, 4: 595.73, 5: 644.63, 6: 587.27, 7: 598.47, 8: 731.97,
        9: 595.87, 10: 669.67, 11: 760.90, 12: 706.17, 13: 617.43, 14: 699.97, 15: 893.8,
        16: 747.47, 17: 750.03, 18: 885.20, 19: 720.03
      },
      record: "11-8-0", finalRank: 6, color: "#FF6B6B"
    },
    "Lance May'd of Steele": {
      weeks: {
        1: 636.6, 2: 667.70, 3: 651.00, 4: 711.03, 5: 652.93, 6: 750.60, 7: 624.57, 8: 908.33,
        9: 656.60, 10: 803.47, 11: 737.33, 12: 758.57, 13: 650.60, 14: 839.80, 15: 722.98,
        16: 672.90, 17: 603.53, 18: 566.43, 19: 696.37
      },
      record: "14-5-0", finalRank: 3, color: "#4ECDC4"
    },
    "carlosc's Swag Team": {
      weeks: {
        1: 601.0, 2: 685.93, 3: 601.57, 4: 550.03, 5: 496.03, 6: 648.67, 7: 595.23, 8: 669.30,
        9: 550.37, 10: 675.80, 11: 652.13, 12: 738.33, 13: 571.47, 14: 686.03, 15: 598.2,
        16: 780.57, 17: 522.20, 18: 594.30, 19: 560.97
      },
      record: "9-10-0", finalRank: 8, color: "#96CEB4"
    },
    "Chris Sale's tender ribcage": {
      weeks: {
        1: 447.3, 2: 523.07, 3: 422.53, 4: 616.13, 5: 513.47, 6: 890.53, 7: 758.53, 8: 696.83,
        9: 590.67, 10: 900.13, 11: 658.63, 12: 809.37, 13: 608.03, 14: 722.80, 15: 580.3,
        16: 508.27, 17: 356.70, 18: 584.93, 19: 442.87
      },
      record: "8-11-0", finalRank: 9, color: "#45B7D1"
    },
    "Don't call it a comeback": {
      weeks: {
        1: 484.7, 2: 374.13, 3: 540.27, 4: 442.53, 5: 499.93, 6: 587.07, 7: 616.80, 8: 826.50,
        9: 733.80, 10: 854.27, 11: 662.27, 12: 585.77, 13: 747.13, 14: 681.07, 15: 763.3,
        16: 678.60, 17: 750.63, 18: 747.73, 19: 765.03
      },
      record: "10-9-0", finalRank: 5, color: "#FFEAA7"
    },
    "Profar So Good": {
      weeks: {
        1: 432.5, 2: 652.63, 3: 643.37, 4: 690.87, 5: 617.00, 6: 862.13, 7: 700.93, 8: 676.43,
        9: 703.13, 10: 577.93, 11: 748.13, 12: 609.03, 13: 639.07, 14: 627.70, 15: 593.4,
        16: 575.63, 17: 514.60, 18: 464.30, 19: 593.93
      },
      record: "6-13-0", finalRank: 10, color: "#DDA0DD"
    },
    "Jansen in the Moonlight": {
      weeks: {
        1: 450.1, 2: 421.13, 3: 650.03, 4: 642.07, 5: 695.33, 6: 647.50, 7: 770.30, 8: 747.90,
        9: 592.73, 10: 890.17, 11: 746.23, 12: 723.93, 13: 664.27, 14: 836.74, 15: 791.4,
        16: 676.73, 17: 671.10, 18: 755.53, 19: 577.73
      },
      record: "10-9-0", finalRank: 7, color: "#FD79A8"
    },
    "Buehler?... Buehler?": {
      weeks: {
        1: 686.1, 2: 706.77, 3: 666.03, 4: 542.47, 5: 692.03, 6: 631.10, 7: 728.70, 8: 643.40,
        9: 726.23, 10: 640.93, 11: 805.23, 12: 768.77, 13: 972.37, 14: 775.17, 15: 699.2,
        16: 812.93, 17: 743.67, 18: 629.27, 19: 586.40
      },
      record: "13-6-0", finalRank: 2, color: "#74B9FF"
    },
    "Whirling Darvishes": {
      weeks: {
        1: 660.5, 2: 595.57, 3: 603.23, 4: 584.43, 5: 541.30, 6: 870.47, 7: 702.10, 8: 699.57,
        9: 799.93, 10: 699.43, 11: 812.20, 12: 598.53, 13: 672.00, 14: 595.10, 15: 671.5,
        16: 696.87, 17: 675.77, 18: 774.37, 19: 710.93
      },
      record: "13-6-0", finalRank: 4, color: "#A29BFE"
    },
    "The Lourdes Sal Judge": {
      weeks: {
        1: 420.3, 2: 538.17, 3: 596.00, 4: 440.87, 5: 586.33, 6: 783.60, 7: 530.20, 8: 734.63,
        9: 871.10, 10: 539.50, 11: 751.50, 12: 735.30, 13: 634.07, 14: 633.77, 15: 768.1,
        16: 857.23, 17: 786.93, 18: 764.13, 19: 820.77
      },
      record: "12-7-0", finalRank: 1, color: "#00B894"
    },
    "Schooop! There It Is": {
      weeks: {
        1: 545.2, 2: 560.37, 3: 612.47, 4: 466.37, 5: 452.27, 6: 404.80, 7: 378.73, 8: 495.67,
        9: 272.40, 10: 435.30, 11: 447.73, 12: 327.37, 13: 411.87, 14: 536.90, 15: 577.8,
        16: 497.40, 17: 431.83, 18: 562.50, 19: 394.60
      },
      record: "4-15-0", finalRank: 11, color: "#E17055"
    },
    "O Greinke Desu Ka?": {
      weeks: {
        1: 459.8, 2: 528.40, 3: 427.47, 4: 523.77, 5: 548.17, 6: 598.07, 7: 483.60, 8: 511.40,
        9: 516.00, 10: 449.10, 11: 444.37, 12: 401.03, 13: 427.20, 14: 283.93, 15: 492.1,
        16: 283.97, 17: 322.97, 18: 319.97, 19: 335.07
      },
      record: "4-15-0", finalRank: 12, color: "#FDCB6E"
    }
  };

  const [selectedTeams, setSelectedTeams] = useState(Object.keys(teams));
  const [sortField, setSortField] = useState('reliabilityScore');
  const [sortDirection, setSortDirection] = useState('desc');

  // Calculate team statistics
  const calculateTeamStats = (teamName, teamData) => {
    const scores = Object.values(teamData.weeks);
    const mean = scores.reduce((sum, score) => sum + score, 0) / scores.length;
    const variance = scores.reduce((sum, score) => sum + Math.pow(score - mean, 2), 0) / scores.length;
    const stdDev = Math.sqrt(variance);
    
    const over700 = scores.filter(score => score >= 700).length;
    const over800 = scores.filter(score => score >= 800).length;
    const under600 = scores.filter(score => score < 600).length;
    
    const recordParts = teamData.record.split('-');
    const wins = parseInt(recordParts[0]);
    const losses = parseInt(recordParts[1]);
    
    // Calculate total points using raw scores (no normalization)
    const rawWeek1Scores = {
      "Kirby's DreamYand": 966.10,
      "Lance May'd of Steele": 1000.97,
      "carlosc's Swag Team": 944.70,
      "Chris Sale's tender ribcage": 703.03,
      "Profar So Good": 680.00,
      "Jansen in the Moonlight": 707.07,
      "Buehler?... Buehler?": 1078.83,
      "Don't call it a comeback": 762.13,
      "Whirling Darvishes": 1038.47,
      "The Lourdes Sal Judge": 660.87,
      "Schooop! There It Is": 857.23,
      "O Greinke Desu Ka?": 722.90
    };
    
    const rawWeek15Scores = {
      "Kirby's DreamYand": 1276.87,
      "Lance May'd of Steele": 1032.83,
      "carlosc's Swag Team": 854.57,
      "Chris Sale's tender ribcage": 829.07,
      "Don't call it a comeback": 1090.47,
      "O Greinke Desu Ka?": 702.93,
      "Jansen in the Moonlight": 1130.60,
      "Schooop! There It Is": 825.47,
      "Profar So Good": 847.70,
      "Buehler?... Buehler?": 998.90,
      "The Lourdes Sal Judge": 1097.27,
      "Whirling Darvishes": 959.33
    };
    
    // Calculate total points with raw Week 1 and 15 scores
    let totalPoints = 0;
    Object.keys(teamData.weeks).forEach(week => {
      const weekNum = parseInt(week);
      if (weekNum === 1) {
        totalPoints += rawWeek1Scores[teamName] || 0;
      } else if (weekNum === 15) {
        totalPoints += rawWeek15Scores[teamName] || 0;
      } else {
        totalPoints += teamData.weeks[week];
      }
    });
    
    // Reliability score: higher average minus penalty for high variance
    const reliabilityScore = mean - (stdDev * 0.3);
    
    const maxScore = Math.max(...scores);
    const minScore = Math.min(...scores);
    const range = maxScore - minScore;
    
    return {
      teamName,
      average: parseFloat(mean.toFixed(1)),
      stdDev: parseFloat(stdDev.toFixed(1)),
      range: parseFloat(range.toFixed(1)),
      totalPoints: parseFloat(totalPoints.toFixed(1)),
      over700,
      over800,
      under600,
      wins,
      losses,
      finalRank: teamData.finalRank,
      reliabilityScore: parseFloat(reliabilityScore.toFixed(1)),
      maxScore,
      minScore,
      winPercentage: parseFloat((wins / (wins + losses) * 100).toFixed(1)),
      weeks: teamData.weeks
    };
  };

  const teamStats = useMemo(() => {
    const baseStats = Object.keys(teams).map(teamName => 
      calculateTeamStats(teamName, teams[teamName])
    );
    
    // Calculate ultimate wins/losses and weekly winners
    const weeks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19];
    const allTeamNames = Object.keys(teams);
    
    return baseStats.map(team => {
      let expectedWins = 0;
      let ultimateWins = 0;
      let weeklyTopScores = 0;
      
      // For each week, count performance metrics
      weeks.forEach(week => {
        if (teams[team.teamName].weeks[week] !== undefined) {
          const teamScore = teams[team.teamName].weeks[week];
          let beatenThisWeek = 0;
          let highestThisWeek = true;
          
          // Check against all other teams
          allTeamNames.forEach(otherTeam => {
            if (otherTeam !== team.teamName && teams[otherTeam].weeks[week] !== undefined) {
              if (teamScore > teams[otherTeam].weeks[week]) {
                beatenThisWeek++;
              }
              // Check if this team had the highest score this week
              if (teams[otherTeam].weeks[week] > teamScore) {
                highestThisWeek = false;
              }
            }
          });
          
          ultimateWins += beatenThisWeek;
          
          // Track weekly winners
          if (highestThisWeek) {
            weeklyTopScores++;
          }
          
          // Convert to expected wins for luck calculation
          const totalOpponents = allTeamNames.length - 1;
          expectedWins += beatenThisWeek / totalOpponents;
        }
      });
      
      const totalPossibleGames = weeks.length * (allTeamNames.length - 1);
      const ultimateLosses = totalPossibleGames - ultimateWins;
      const luckFactor = team.wins - expectedWins;
      
      return {
        ...team,
        expectedWins: parseFloat(expectedWins.toFixed(1)),
        luckFactor: parseFloat(luckFactor.toFixed(1)),
        ultimateWins,
        ultimateLosses,
        weeklyTopScores
      };
    });
  }, []);

  // Sort teams
  const sortedTeamStats = useMemo(() => {
    return [...teamStats].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      
      if (sortDirection === 'desc') {
        return bVal - aVal;
      } else {
        return aVal - bVal;
      }
    });
  }, [teamStats, sortField, sortDirection]);

  // Prepare data for chart
  const chartData = useMemo(() => {
    const weeks = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19];
    return weeks.map(week => {
      const weekData = { week };
      selectedTeams.forEach(teamName => {
        if (teams[teamName].weeks[week] !== undefined) {
          weekData[teamName] = teams[teamName].weeks[week];
        }
      });
      return weekData;
    });
  }, [selectedTeams]);

  // Calculate Y-axis bounds intelligently
  const yAxisBounds = useMemo(() => {
    if (selectedTeams.length === 0) return { min: 300, max: 1000 };
    
    let allScores = [];
    selectedTeams.forEach(teamName => {
      allScores = allScores.concat(Object.values(teams[teamName].weeks));
    });
    
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

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'desc' ? 'asc' : 'desc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getSortIcon = (field) => {
    if (sortField !== field) return '↕️';
    return sortDirection === 'desc' ? '↓' : '↑';
  };

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Fantasy Baseball 2022 Season Dashboard</h1>
      
      {/* Normalization Notice */}
      <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
        <div className="flex">
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              <strong>Data Normalization:</strong> Week 1 (11 days) and Week 15 (10 days) scores have been normalized to 7-day equivalents for fair comparison. 
              Week 1 scores × 0.636, Week 15 scores × 0.700. Season ran 19 weeks.
            </p>
          </div>
        </div>
      </div>
      
      {/* Team Selection */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Select Teams to Display</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          {Object.keys(teams).map(teamName => (
            <label key={teamName} className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={selectedTeams.includes(teamName)}
                onChange={() => handleTeamToggle(teamName)}
                className="w-4 h-4 text-blue-600"
              />
              <span className="text-sm text-gray-700 truncate">{teamName}</span>
            </label>
          ))}
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
        </div>
      </div>

      {/* Weekly Scores Chart */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Weekly Scores Trend</h2>
        <div className="h-96">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" />
              <YAxis domain={[yAxisBounds.min, yAxisBounds.max]} />
              <Tooltip 
                formatter={(value, name) => [value?.toFixed(1), name]}
                labelFormatter={(label) => `Week ${label}`}
              />
              <Legend />
              {selectedTeams.map(teamName => (
                <Line
                  key={teamName}
                  type="monotone"
                  dataKey={teamName}
                  stroke={teams[teamName].color}
                  strokeWidth={2}
                  dot={{ r: 4 }}
                  connectNulls={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Statistics Table */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Team Statistics</h2>
        <div className="overflow-x-auto">
          <table className="w-full table-auto">
            <thead>
              <tr className="bg-gray-100">
                <th 
                  className="px-4 py-2 text-left cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('teamName')}
                >
                  Team {getSortIcon('teamName')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('average')}
                >
                  Avg Score {getSortIcon('average')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('totalPoints')}
                >
                  Total Points {getSortIcon('totalPoints')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('stdDev')}
                >
                  Std Dev {getSortIcon('stdDev')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('range')}
                >
                  Range {getSortIcon('range')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('reliabilityScore')}
                >
                  Reliability {getSortIcon('reliabilityScore')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('wins')}
                >
                  Wins {getSortIcon('wins')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('losses')}
                >
                  Losses {getSortIcon('losses')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('winPercentage')}
                >
                  Win % {getSortIcon('winPercentage')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('over700')}
                >
                  700+ Games {getSortIcon('over700')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('over800')}
                >
                  800+ Games {getSortIcon('over800')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('under600')}
                >
                  Under 600 {getSortIcon('under600')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('maxScore')}
                >
                  Best Game {getSortIcon('maxScore')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('minScore')}
                >
                  Worst Game {getSortIcon('minScore')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('finalRank')}
                >
                  Final Rank {getSortIcon('finalRank')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('luckFactor')}
                >
                  Luck Factor {getSortIcon('luckFactor')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('ultimateWins')}
                >
                  Ultimate Wins {getSortIcon('ultimateWins')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('ultimateLosses')}
                >
                  Ultimate Losses {getSortIcon('ultimateLosses')}
                </th>
                <th 
                  className="px-4 py-2 text-center cursor-pointer hover:bg-gray-200"
                  onClick={() => handleSort('weeklyTopScores')}
                >
                  Weekly Wins {getSortIcon('weeklyTopScores')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedTeamStats.map((team, index) => (
                <tr key={team.teamName} className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                  <td className="px-4 py-2 font-medium">{team.teamName}</td>
                  <td className="px-4 py-2 text-center">{team.average}</td>
                  <td className="px-4 py-2 text-center font-semibold text-green-600">{team.totalPoints}</td>
                  <td className="px-4 py-2 text-center">{team.stdDev}</td>
                  <td className="px-4 py-2 text-center">{team.range}</td>
                  <td className="px-4 py-2 text-center font-semibold text-blue-600">{team.reliabilityScore}</td>
                  <td className="px-4 py-2 text-center text-green-600">{team.wins}</td>
                  <td className="px-4 py-2 text-center text-red-600">{team.losses}</td>
                  <td className="px-4 py-2 text-center">{team.winPercentage}%</td>
                  <td className="px-4 py-2 text-center">{team.over700}</td>
                  <td className="px-4 py-2 text-center">{team.over800}</td>
                  <td className="px-4 py-2 text-center">{team.under600}</td>
                  <td className="px-4 py-2 text-center text-green-600">{team.maxScore}</td>
                  <td className="px-4 py-2 text-center text-red-600">{team.minScore}</td>
                  <td className="px-4 py-2 text-center">#{team.finalRank}</td>
                  <td className="px-4 py-2 text-center">
                    <span className={team.luckFactor > 0 ? 'text-green-600' : team.luckFactor < 0 ? 'text-red-600' : 'text-gray-600'}>
                      {team.luckFactor > 0 ? '+' : ''}{team.luckFactor}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-center text-blue-600 font-semibold">{team.ultimateWins}</td>
                  <td className="px-4 py-2 text-center text-red-600">{team.ultimateLosses}</td>
                  <td className="px-4 py-2 text-center text-green-600 font-semibold">{team.weeklyTopScores}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Key Insights */}
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        <h2 className="text-xl font-semibold mb-4">Key Insights</h2>
        
        {/* Primary Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-800">Most Reliable Team</h3>
            <p className="text-blue-600">
              {teamStats.reduce((prev, current) => (prev.reliabilityScore > current.reliabilityScore) ? prev : current).teamName}
            </p>
            <p className="text-sm text-blue-500">
              High average + low variance
            </p>
          </div>
          
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="font-semibold text-green-800">Highest Total Points</h3>
            <p className="text-green-600">
              {teamStats.reduce((prev, current) => (prev.totalPoints > current.totalPoints) ? prev : current).teamName}
            </p>
            <p className="text-sm text-green-500">
              {teamStats.reduce((prev, current) => (prev.totalPoints > current.totalPoints) ? prev : current).totalPoints} total points
            </p>
          </div>
          
          <div className="bg-lime-50 p-4 rounded-lg">
            <h3 className="font-semibold text-lime-800">Highest Average</h3>
            <p className="text-lime-600">
              {teamStats.reduce((prev, current) => (prev.average > current.average) ? prev : current).teamName}
            </p>
            <p className="text-sm text-lime-500">
              {teamStats.reduce((prev, current) => (prev.average > current.average) ? prev : current).average} points/game
            </p>
          </div>
          
          <div className="bg-purple-50 p-4 rounded-lg">
            <h3 className="font-semibold text-purple-800">Most Consistent</h3>
            <p className="text-purple-600">
              {teamStats.reduce((prev, current) => (prev.stdDev < current.stdDev) ? prev : current).teamName}
            </p>
            <p className="text-sm text-purple-500">
              Std dev: {teamStats.reduce((prev, current) => (prev.stdDev < current.stdDev) ? prev : current).stdDev}
            </p>
          </div>
        </div>
        
        {/* Performance Categories Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-emerald-50 p-4 rounded-lg">
            <h3 className="font-semibold text-emerald-800">Most 700+ Games</h3>
            <p className="text-emerald-600">
              {teamStats.reduce((prev, current) => (prev.over700 > current.over700) ? prev : current).teamName}
            </p>
            <p className="text-sm text-emerald-500">
              {teamStats.reduce((prev, current) => (prev.over700 > current.over700) ? prev : current).over700} games over 700
            </p>
          </div>
          
          <div className="bg-teal-50 p-4 rounded-lg">
            <h3 className="font-semibold text-teal-800">Most 800+ Games</h3>
            <p className="text-teal-600">
              {teamStats.reduce((prev, current) => (prev.over800 > current.over800) ? prev : current).teamName}
            </p>
            <p className="text-sm text-teal-500">
              {teamStats.reduce((prev, current) => (prev.over800 > current.over800) ? prev : current).over800} elite performances
            </p>
          </div>
          
          <div className="bg-red-50 p-4 rounded-lg">
            <h3 className="font-semibold text-red-800">Most Under 600</h3>
            <p className="text-red-600">
              {teamStats.reduce((prev, current) => (prev.under600 > current.under600) ? prev : current).teamName}
            </p>
            <p className="text-sm text-red-500">
              {teamStats.reduce((prev, current) => (prev.under600 > current.under600) ? prev : current).under600} struggles
            </p>
          </div>
          
          <div className="bg-orange-50 p-4 rounded-lg">
            <h3 className="font-semibold text-orange-800">Most Volatile</h3>
            <p className="text-orange-600">
              {teamStats.reduce((prev, current) => (prev.range > current.range) ? prev : current).teamName}
            </p>
            <p className="text-sm text-orange-500">
              {teamStats.reduce((prev, current) => (prev.range > current.range) ? prev : current).range} point range
            </p>
          </div>
        </div>
        
        {/* Ultimate Performance Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <h3 className="font-semibold text-blue-800">Most Ultimate Wins</h3>
            <p className="text-blue-600">
              {teamStats.reduce((prev, current) => (prev.ultimateWins > current.ultimateWins) ? prev : current).teamName}
            </p>
            <p className="text-sm text-blue-500">
              {teamStats.reduce((prev, current) => (prev.ultimateWins > current.ultimateWins) ? prev : current).ultimateWins} wins vs all teams
            </p>
          </div>
          
          <div className="bg-amber-50 p-4 rounded-lg">
            <h3 className="font-semibold text-amber-800">Most Weekly Wins</h3>
            <p className="text-amber-600">
              {teamStats.reduce((prev, current) => (prev.weeklyTopScores > current.weeklyTopScores) ? prev : current).teamName}
            </p>
            <p className="text-sm text-amber-500">
              {teamStats.reduce((prev, current) => (prev.weeklyTopScores > current.weeklyTopScores) ? prev : current).weeklyTopScores} weeks as top scorer
            </p>
          </div>
          
          <div className="bg-slate-50 p-4 rounded-lg">
            <h3 className="font-semibold text-slate-800">Ultimate Win %</h3>
            <p className="text-slate-600">
              {teamStats.reduce((prev, current) => {
                const prevPct = prev.ultimateWins / (prev.ultimateWins + prev.ultimateLosses);
                const currentPct = current.ultimateWins / (current.ultimateWins + current.ultimateLosses);
                return prevPct > currentPct ? prev : current;
              }).teamName}
            </p>
            <p className="text-sm text-slate-500">
              Best overall record vs all
            </p>
          </div>
        </div>
        
        {/* Luck Analysis Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="bg-green-50 p-4 rounded-lg">
            <h3 className="font-semibold text-green-800">Luckiest Team</h3>
            <p className="text-green-600">
              {teamStats.reduce((prev, current) => (prev.luckFactor > current.luckFactor) ? prev : current).teamName}
            </p>
            <p className="text-sm text-green-500">
              +{teamStats.reduce((prev, current) => (prev.luckFactor > current.luckFactor) ? prev : current).luckFactor} more wins than expected
            </p>
          </div>
          
          <div className="bg-red-50 p-4 rounded-lg">
            <h3 className="font-semibold text-red-800">Unluckiest Team</h3>
            <p className="text-red-600">
              {teamStats.reduce((prev, current) => (prev.luckFactor < current.luckFactor) ? prev : current).teamName}
            </p>
            <p className="text-sm text-red-500">
              {teamStats.reduce((prev, current) => (prev.luckFactor < current.luckFactor) ? prev : current).luckFactor} fewer wins than expected
            </p>
          </div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="font-semibold text-gray-800 mb-2">2022 Season Analysis</h3>
          <p className="text-sm text-gray-600 mb-2">
            Complete 19-week 2022 season with normalized scoring for extended weeks. The reliability score combines average performance with consistency, 
            making it the best predictor of head-to-head matchup success.
          </p>
          <p className="text-sm text-gray-600">
            <strong>Ultimate Wins/Losses:</strong> Results if everyone played everyone each week (19 weeks × 11 opponents = 209 total games per team). 
            <strong>Weekly Wins:</strong> Number of weeks each team scored the highest. 
            <strong>Luck Factor:</strong> Actual wins minus expected wins based on scoring performance - positive values indicate favorable scheduling.
          </p>
        </div>
      </div>
    </div>
  );
};

export default FantasyFootballDashboard;