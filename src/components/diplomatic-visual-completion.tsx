type FlagCropFrameProps = {
  src: string
  alt: string
  className?: string
}

export function FlagCropFrame({src,alt,className=''}:FlagCropFrameProps) {
  return <div className={`flag-crop-frame ${className}`.trim()}>
    <img className="flag-crop-image" src={src} alt={alt} />
  </div>
}

export function DiplomaticFooterBand() {
  return <div className="footer-national-band" aria-hidden="true"><span/><span/><span/></div>
}
