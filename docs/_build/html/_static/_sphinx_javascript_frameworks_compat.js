/* Compatability shim for jQuery and underscores.js.
 *
 * Copyright Sphinx contributors
 * Released under the two clause BSD licence
 */

/**
 * small helper function to urldecode strings
 *
 * See https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/decodeURIComponent#Decoding_query_parameters_from_a_URL
 */
import jQuery from 'jquery'
jQuery.urldecode = function (x) {
  if (!x) {
    return x
  }
  return decodeURIComponent(x.replace(/\+/g, ' '))
}

/**
 * small helper function to urlencode strings
 */
jQuery.urlencode = encodeURIComponent

/**
 * This function returns the parsed url parameters of the
 * current request. Multiple values per key are supported,
 * it will always return arrays of strings for the value parts.
 */
jQuery.getQueryParameters = function (s) {
  if (typeof s === 'undefined') { s = document.location.search }
  const parts = s.substr(s.indexOf('?') + 1).split('&')
  const result = {}
  for (let i = 0; i < parts.length; i++) {
    const tmp = parts[i].split('=', 2)
    const key = jQuery.urldecode(tmp[0])
    const value = jQuery.urldecode(tmp[1])
    if (key in result) { result[key].push(value) } else { result[key] = [value] }
  }
  return result
}

/**
 * highlight a given string on a jquery object by wrapping it in
 * span elements with the given class name.
 */
jQuery.fn.highlightText = function (text, className) {
  function highlight (node, addItems) {
    if (node.nodeType === 3) {
      const val = node.nodeValue
      const pos = val.toLowerCase().indexOf(text)
      if (pos >= 0 &&
                !jQuery(node.parentNode).hasClass(className) &&
                !jQuery(node.parentNode).hasClass('nohighlight')) {
        let span
        const isInSVG = jQuery(node).closest('body, svg, foreignObject').is('svg')
        if (isInSVG) {
          span = document.createElementNS('http://www.w3.org/2000/svg', 'tspan')
        } else {
          span = document.createElement('span')
          span.className = className
        }
        span.appendChild(document.createTextNode(val.substr(pos, text.length)))
        node.parentNode.insertBefore(span, node.parentNode.insertBefore(
          document.createTextNode(val.substr(pos + text.length)),
          node.nextSibling))
        node.nodeValue = val.substr(0, pos)
        if (isInSVG) {
          const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
          const bbox = node.parentElement.getBBox()
          rect.x.baseVal.value = bbox.x
          rect.y.baseVal.value = bbox.y
          rect.width.baseVal.value = bbox.width
          rect.height.baseVal.value = bbox.height
          rect.setAttribute('class', className)
          addItems.push({
            parent: node.parentNode,
            target: rect
          })
        }
      }
    } else if (!jQuery(node).is('button, select, textarea')) {
      jQuery.each(node.childNodes, function () {
        highlight(this, addItems)
      })
    }
  }
  const addItems = []
  const result = this.each(function () {
    highlight(this, addItems)
  })
  for (let i = 0; i < addItems.length; ++i) {
    jQuery(addItems[i].parent).before(addItems[i].target)
  }
  return result
}

/*
 * backward compatibility for jQuery.browser
 * This will be supported until firefox bug is fixed.
 */
if (!jQuery.browser) {
  jQuery.uaMatch = function (ua) {
    ua = ua.toLowerCase()

    const match = /(chrome)[ \/]([\w.]+)/.exec(ua) ||
            /(webkit)[ \/]([\w.]+)/.exec(ua) ||
            /(opera)(?:.*version|)[ \/]([\w.]+)/.exec(ua) ||
            /(msie) ([\w.]+)/.exec(ua) ||
            ua.indexOf('compatible') < 0 && /(mozilla)(?:.*? rv:([\w.]+)|)/.exec(ua) ||
            []

    return {
      browser: match[1] || '',
      version: match[2] || '0'
    }
  }
  jQuery.browser = {}
  jQuery.browser[jQuery.uaMatch(navigator.userAgent).browser] = true
}
