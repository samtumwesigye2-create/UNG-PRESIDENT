const VP_IDENTITY_PLATE='https://assets.macaly-user-data.dev/cdn-cgi/image/format=webp,width=2000,height=2000,fit=scale-down,quality=85,anim=false/w5xb3too087c17afd6dv9mov/es9cbxmoiix2ab2r0cemhfzx/cMhdH8PnCuRMUuhn-17ua.png'
const VP_FLAG='https://assets.macaly-user-data.dev/cdn-cgi/image/format=webp,width=2000,height=2000,fit=scale-down,quality=85,anim=false/w5xb3too087c17afd6dv9mov/es9cbxmoiix2ab2r0cemhfzx/GUw1ndiVyLrDsjz-TCzjF.jpeg'

export function VicePresidentSeal({className=''}:{className?:string}){
  return <span
    className={`vp-seal-from-identity-plate ${className}`}
    role="img"
    aria-label="Vice President of the Republic of Uganda seal"
    style={{backgroundImage:`url(${VP_IDENTITY_PLATE})`}}
  />
}

export function VicePresidentialFlag(){
  return <div className="vp-flag-frame">
    <img src={VP_FLAG} alt="Vice Presidential flag" data-asset="IMG_2538-vice-presidential-flag" />
    <div className="vp-flag-seal-cover" aria-hidden="true">
      <VicePresidentSeal className="h-full w-full" />
    </div>
  </div>
}
