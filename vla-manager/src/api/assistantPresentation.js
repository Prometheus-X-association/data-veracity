export function normaliseAssistantExamples (examples) {
  const source = examples && typeof examples === 'object' && !Array.isArray(examples)
    ? examples
    : {}

  return {
    passing: toList(source.passing),
    failing: toList(source.failing)
  }
}

export function formatAssistantJson (value) {
  if (typeof value === 'string') return value

  try {
    return JSON.stringify(value, null, 2)
  } catch {
    return String(value)
  }
}

export function tokeniseAssistantJson (value) {
  const text = String(formatAssistantJson(value) ?? '')
  const tokens = []
  let index = 0

  while (index < text.length) {
    const character = text[index]

    if (character === '"') {
      const start = index
      index += 1
      while (index < text.length) {
        if (text[index] === '\\') {
          index += 2
        } else if (text[index] === '"') {
          index += 1
          break
        } else {
          index += 1
        }
      }
      const isKey = /^\s*:/.test(text.slice(index))
      tokens.push({ text: text.slice(start, index), type: isKey ? 'key' : 'string' })
      continue
    }

    if (/[-0-9]/.test(character)) {
      const match = text.slice(index).match(/^-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?/)
      if (match) {
        tokens.push({ text: match[0], type: 'number' })
        index += match[0].length
        continue
      }
    }

    const literal = text.slice(index).match(/^(true|false|null)\b/)
    if (literal) {
      tokens.push({ text: literal[0], type: literal[1] === 'null' ? 'null' : 'boolean' })
      index += literal[0].length
      continue
    }

    if ('{}[],:'.includes(character)) {
      tokens.push({ text: character, type: 'punctuation' })
      index += 1
      continue
    }

    const start = index
    while (index < text.length && !/["{}\[\],:\s]/.test(text[index])) index += 1
    if (start === index) index += 1
    tokens.push({ text: text.slice(start, index), type: 'plain' })
  }

  return tokens
}

export function assistantTextChunks (value) {
  return String(value ?? '').match(/\s+|\S+\s*/g) || []
}

function toList (value) {
  if (value === undefined || value === null) return []
  return Array.isArray(value) ? value : [value]
}
