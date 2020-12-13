import React, { lazy } from 'react'
import { isAuthorised } from '../utils/auth'
import { getAuth } from '../utils/auth'

const config = {
  auth: {
    isAuthenticated: isAuthorised,
    getData: () => {
      return getAuth()
    },
    signInURL: '/signin',
  },
}

export default config
