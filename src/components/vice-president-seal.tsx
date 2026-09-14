import { NATIONAL_FLAG_DATA_URI, VICE_PRESIDENTIAL_SEAL_DATA_URI } from '../lib/presidential-assets'

export function VicePresidentSeal({className=''}:{className?:string}){
  return <span className={`vp-seal-from-identity-plate ${className}`} role="img" aria-label="Vice President of the Republic of Uganda seal">
    <img src={VICE_PRESIDENTIAL_SEAL_DATA_URI} alt="Vice President of the Republic of Uganda seal" />
  </span>
}

export function VicePresidentialFlag(){
  return <div className="vp-flag-frame">
    <img src={NATIONAL_FLAG_DATA_URI} alt="Vice Presidential flag field" />
    <div className="vp-flag-seal-cover" aria-hidden="true"><VicePresidentSeal className="h-full w-full" /></div>
  </div>
}
