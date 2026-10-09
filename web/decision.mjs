/* Fail closed: community model values only; matches need independently verified context. */
export function compareBuilds(a,b){
 if(!a||!b)return {comparable:false,reasons:['Select two source-linked builds.'],modeledDelta:null};
 const reasons=[];
 if(a.characterClass!==b.characterClass)reasons.push('Character classes differ');
 if(a.level!==b.level)reasons.push('Character levels differ');
 if(a.buildType!==b.buildType)reasons.push('Build roles differ');
 if(a.snapshotDate!==b.snapshotDate)reasons.push('Snapshots differ');
 if(a.benchmarkDps==null||b.benchmarkDps==null)reasons.push('At least one modeled DPS is absent');
 if(!a.scenarioFingerprint||a.scenarioFingerprint!==b.scenarioFingerprint)reasons.push('Same boss, buffs, encounter and rotation not verified');
 if(!a.equipmentFingerprint||a.equipmentFingerprint!==b.equipmentFingerprint)reasons.push('Equipment/stat control not verified');
 if(!a.modelVersion||a.modelVersion!==b.modelVersion)reasons.push('Calculator model versions not matched');
 return {comparable:!reasons.length,reasons,modeledDelta:reasons.length?null:b.benchmarkDps-a.benchmarkDps};
}
