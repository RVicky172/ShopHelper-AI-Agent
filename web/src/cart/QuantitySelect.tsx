import { MAX_QUANTITY } from './cartLogic'

export function QuantitySelect({
  value,
  onChange,
  label,
}: {
  value: number
  onChange: (quantity: number) => void
  label: string
}) {
  return (
    <select
      aria-label={label}
      value={value}
      onChange={(event) => onChange(Number(event.target.value))}
      className="min-h-11 rounded border border-field bg-paper px-2"
    >
      {Array.from({ length: MAX_QUANTITY }, (_, index) => (
        <option key={index + 1} value={index + 1}>
          {index + 1}
        </option>
      ))}
    </select>
  )
}
