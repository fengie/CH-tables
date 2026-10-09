/* Tested pure arithmetic for a dated shop snapshot; currency and unknowns stay separate. */
const valid=(n,max)=>Number.isSafeInteger(n)&&n>=0&&n<=max;
const gcd=(a,b)=>b?gcd(b,a%b):a;
export function cheapestQuna(packs,target){
 if(!valid(target,100000))throw RangeError('Invalid Quna target');
 if(!target)return {costCents:0,quna:0,mileage:0,packs:{},transactions:0};
 if(!Array.isArray(packs)||!packs.length||packs.some(p=>!valid(p.quna,100000)||p.quna===0||!valid(p.usd_cents,1000000)||p.usd_cents===0||!valid(p.mileage,1000000)))throw Error('Invalid pack catalog');
 const unit=packs.map(p=>p.quna).reduce(gcd);
 const maxQ=Math.ceil((target+Math.max(...packs.map(p=>p.quna))-1)/unit);
 const dp=Array(maxQ+1).fill(null);
 dp[0]={cost:0,count:0,mileage:0,steps:[]};
 for(let q=0;q<=maxQ;q++){
   if(!dp[q])continue;
   for(let i=0;i<packs.length;i++){
     const next=q+packs[i].quna/unit;if(next>maxQ)continue;
     const prev=dp[q],v={cost:prev.cost+packs[i].usd_cents,count:prev.count+1,mileage:prev.mileage+packs[i].mileage,steps:[...prev.steps,i]};
     if(!dp[next]||v.cost<dp[next].cost||(v.cost===dp[next].cost&&v.count<dp[next].count))dp[next]=v;
   }
 }
 let winner=null;
 for(let q=Math.ceil(target/unit);q<=maxQ;q++){
   const v=dp[q];if(!v)continue;
   if(!winner||v.cost<winner.cost||(v.cost===winner.cost&&(q*unit<winner.quna||(q*unit===winner.quna&&v.count<winner.count))))
     winner={...v,quna:q*unit};
 }
 if(!winner)throw Error('Cannot satisfy desired Quna');
 const quantities={};
 for(const i of winner.steps)quantities[packs[i].id]=(quantities[packs[i].id]||0)+1;
 return {costCents:winner.cost,quna:winner.quna,mileage:winner.mileage,packs:quantities,transactions:winner.count};
}
export function wardrobeQuote(catalog,opts={}){
 if(!catalog||!Array.isArray(catalog.products)||!Array.isArray(catalog.packs))throw Error('Shop data missing');
 const wanted=new Set(opts.wanted||[]),owned=new Set(opts.owned||[]);
 const wallet=opts.walletQuna??0,changes=opts.dyeChanges??0,perDye=opts.dyeQunaEach??null,budget=opts.budgetCents??null;
 if(!valid(wallet,100000)||!valid(changes,50)||!(perDye===null||valid(perDye,10000))||!(budget===null||valid(budget,10000000)))throw RangeError('Invalid inputs');
 const ids=new Set(catalog.products.map(p=>p.id));for(const id of [...wanted,...owned])if(!ids.has(id))throw Error('Unknown item '+id);
 const remaining=catalog.products.filter(p=>wanted.has(p.id)&&!owned.has(p.id));
 let cashDirect=0,qunaNeed=0,knownMileage=0,unknown=[];
 for(const p of remaining){
   if(p.category==='Earned in-game'){unknown.push(p.name+': Kina cost / offer not verified');continue;}
   if(p.usd_cents===null&&p.quna===null){unknown.push(p.name+': price unknown');continue;}
   if(p.usd_cents!==null){if(!valid(p.usd_cents,1000000))throw Error('Invalid price');cashDirect+=p.usd_cents;}
   if(p.quna!==null){if(!valid(p.quna,100000))throw Error('Invalid Quna');qunaNeed+=p.quna;}
   if(p.mileage===null)unknown.push(p.name+': Mileage not verified');
   else if(valid(p.mileage,1000000))knownMileage+=p.mileage;
   else throw Error('Invalid Mileage');
 }
 if(changes){if(perDye===null)unknown.push('Dye costs not entered');else qunaNeed+=changes*perDye;}
 const topup=cheapestQuna(catalog.packs,Math.max(0,qunaNeed-wallet));
 const subtotalCents=cashDirect+topup.costCents;
 return {wanted:[...wanted],owned:[...owned],remaining:remaining.map(p=>p.id),cashDirect,qunaNeed,topup,subtotalCents,
   knownMileage:knownMileage+topup.mileage,mileageIncomplete:unknown.some(x=>x.includes('Mileage')),unknown,
   balanceQuna:wallet+topup.quna-qunaNeed,
   budgetStatus:budget===null?'not-set':unknown.some(x=>/price unknown|Dye costs/.test(x))?'incomplete':subtotalCents<=budget?'within':'over'};
}
