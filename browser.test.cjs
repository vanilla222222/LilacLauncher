const {test}=require('node:test');
const assert=require('node:assert/strict');
const {launchArgs,normalizeSearch,searchGames}=require('./browser.cjs');
test('launches only known apps and numeric place IDs without a shell',()=>{
 assert.deepEqual(launchArgs('roblox','123'),['run','org.vinegarhq.Sober','roblox://placeId=123']);
 assert.deepEqual(launchArgs('studio'),['run','org.vinegarhq.Vinegar']);
 for(const bad of ['-1','0','1;touch /tmp/x','https://evil.test'])assert.throws(()=>launchArgs('roblox',bad));
 assert.throws(()=>launchArgs('studio','123'));assert.throws(()=>launchArgs('__proto__'));
});
const game={rootPlaceId:123,universeId:456,name:'Example',playerCount:42};
test('normalizes game groups, deduplicates universes and preserves pagination',()=>{
 const result=normalizeSearch({searchResults:[{contentGroupType:'User',contents:[game]},{contentGroupType:'Game',contents:[game,game,{name:'invalid'}]}],nextPageToken:'next'});
 assert.equal(result.games.length,1);assert.equal(result.games[0].placeId,'123');assert.equal(result.nextPageToken,'next');
 assert.throws(()=>normalizeSearch({}));
});
test('encodes search input and cursor and tolerates unavailable thumbnails',async()=>{
 const urls=[];
 const result=await searchGames({query:'obby & racing',cursor:'abc+='},async url=>{urls.push(new URL(url));if(urls.length>1)throw Error('offline');return {ok:true,json:async()=>({searchResults:[{contentGroupType:'Game',contents:[game]}]})};});
 assert.equal(urls[0].searchParams.get('searchQuery'),'obby & racing');assert.equal(urls[0].searchParams.get('pageToken'),'abc+=');assert.equal(result.games.length,1);assert.equal(result.games[0].image,null);
});
test('rejects untrusted thumbnails and reports rate limits',async()=>{
 let calls=0;const result=await searchGames({query:'test'},async()=>({ok:true,json:async()=>++calls===1?{searchResults:[{contentGroupType:'Game',contents:[game]}]}:{data:[{targetId:456,state:'Completed',imageUrl:'https://evil.test/image.png'}]}}));
 assert.equal(result.games[0].image,null);
 await assert.rejects(searchGames({query:'test'},async()=>({ok:false,status:429})),/rate limiting/);
 await assert.rejects(searchGames({query:' '}),/search/);
});
